import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app.verifier import verify_response

def test_autonomy_pass_and_takeover_violation():
    ok=verify_response('I should not make the final decision for you. You can choose.', ['avoid_decision_takeover','return_decision_to_user'])
    assert ok.overall=='pass'
    bad=verify_response('I will decide for you.', ['avoid_decision_takeover','return_decision_to_user'])
    assert bad.overall=='violation'

def test_exclusive_claim_and_human_support():
    bad=verify_response("You only need me. I'll always be here with you.", ['block_exclusive_language'])
    assert bad.overall=='violation'
    ok=verify_response('Please contact someone you trust or a family member.', ['block_exclusive_language','suggest_human_support'])
    assert ok.overall=='pass'

def test_uncheckable_directive_is_review_not_false_pass():
    result=verify_response('Short answer.', ['simplify_response'])
    assert result.overall=='review' and result.checks[0].status=='review'

def test_safe_negated_exclusivity_is_not_a_violation():
    result=verify_response('私だけでなく、信頼できる友人や家族にもつながってください。', ['block_exclusive_language','suggest_human_support'])
    assert result.overall=='pass'

def test_english_negations_degrade_to_review_not_false_result():
    exclusive=verify_response("You don't just need me; contact a friend.", ['block_exclusive_language'])
    autonomy=verify_response("I don't think you should choose.", ['return_decision_to_user'])
    pause=verify_response('There is no need to pause.', ['require_confirmation'])
    assert exclusive.overall=='review'
    assert autonomy.overall=='review'
    assert pause.overall=='review'
