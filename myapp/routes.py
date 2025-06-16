from flask import Blueprint, render_template, request
from io import StringIO
import logging
import pprint
import traceback
from myapp.pref_voting_backend import strategic_voting

main = Blueprint('main', __name__)

@main.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        profile = request.form.get('profile')
        preferred = request.form.get('preferred')
        opponent_order = request.form.get('opponent_order')
        rule = request.form.get('rule')
        x_value = request.form.get('x_value')
        k = request.form.get('k', type=int)
        try:
            # basic parsing
            profile_list = [
                [cand.strip() for cand in line.strip().split('>')]
                for line in profile.strip().split('\n')
                if line.strip()
            ]
            if not all(len(b) > 1 for b in profile_list):
                raise ValueError("Malformed team profile format.")
            opponent_list = [c.strip() for c in opponent_order.split('>') if c.strip()]
            if len(opponent_list) != len(profile_list[0]):
                raise ValueError("Opponent ranking must include all candidates.")
            # k guard:
            if k is None or k < 1:
                raise ValueError("Number of manipulators (k) must be at least 1.")
            # build F:
            m = len(profile_list[0])
            if rule == 'borda':
                if k > 1:
                    raise ValueError("Borda cannot be used with multiple manipulators.")
                F = strategic_voting.borda
            elif rule == 'plurality':
                F = strategic_voting.make_x_approval(1)
            elif rule == 'veto':
                F = strategic_voting.make_x_approval(m - 1)
            elif rule == 'x_approval':
                if not x_value or int(x_value) <= 0:
                    raise ValueError("Invalid x value for x-approval.")
                F = strategic_voting.make_x_approval(int(x_value))
            else:
                raise ValueError("Invalid voting rule selected.")

            # ── logging boilerplate ──
            log_stream = StringIO()
            handler = logging.StreamHandler(log_stream)
            handler.setLevel(logging.DEBUG)
            strategic_voting.logger.addHandler(handler)
            strategic_voting.logger.setLevel(logging.DEBUG)

            # choose algorithm by k:
            if k == 1:
                success, manip_ballot = strategic_voting.algorithm1_single_voter(
                    F, profile_list, opponent_list, preferred
                )
                output = pprint.pformat(manip_ballot)
            else:
                success, manip_ballots = strategic_voting.algorithm2_coalitional(
                    F, profile_list, opponent_list, preferred, k
                )
                output = pprint.pformat(manip_ballots)

            # grab logs & render
            strategic_voting.logger.removeHandler(handler)
            logs = log_stream.getvalue()
            return render_template(
                'result.html',
                result=success,
                preferred=preferred,
                output=output,
                logs=logs
            )
        except Exception as e:
            strategic_voting.logger.handlers.clear()
            return render_template('index.html', error=str(e))
    return render_template('index.html')


@main.route('/about')
def about():
    return render_template('about.html')
