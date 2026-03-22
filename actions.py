import logging

logger = logging.getLogger(__name__)

AVAILABLE_ACTIONS = {
    'answer_1': 'Again（重来）',
    'answer_2': 'Hard（困难）',
    'answer_3': 'Good（良好）',
    'answer_4': 'Easy（简单）',
    'replay_audio': '重放音频',
    'undo': '撤回',
    'show_answer': '显示答案',
    'none': '无操作',
}


def execute_action(action_name):
    try:
        from aqt import mw
    except ImportError:
        logger.error('Anki not available')
        return False

    if not mw:
        return False

    if action_name == 'none' or not action_name:
        return True

    if action_name.startswith('answer_'):
        return _answer_card(action_name)
    elif action_name == 'replay_audio':
        return _replay_audio()
    elif action_name == 'undo':
        return _undo()
    elif action_name == 'show_answer':
        return _show_answer()
    else:
        logger.warning('Unknown action: %s', action_name)
        return False


def _answer_card(action_name):
    from aqt import mw

    reviewer = mw.reviewer
    if not reviewer:
        return False

    if mw.state != 'review':
        return False

    # First press: show the answer (flip card)
    if reviewer.state == 'question':
        reviewer._showAnswer()
        logger.debug('Showed answer (flip to back)')
        return 'show_answer'

    # Second press: actually answer the card
    if reviewer.state != 'answer':
        return False

    try:
        ease_num = int(action_name.split('_')[1])
    except (IndexError, ValueError):
        return False

    button_count = mw.col.sched.answerButtons(reviewer.card)
    if ease_num > button_count:
        ease_num = button_count

    if ease_num < 1:
        ease_num = 1

    reviewer._answerCard(ease_num)
    logger.debug('Answered card with ease %d', ease_num)
    return True


def _replay_audio():
    from aqt import mw

    reviewer = mw.reviewer
    if not reviewer or mw.state != 'review':
        return False

    try:
        mw.reviewer.replayAudio()
        logger.debug('Replayed audio')
        return True
    except Exception as e:
        logger.debug('Replay audio failed: %s', e)
        return False


def _undo():
    from aqt import mw

    try:
        if hasattr(mw, 'undo'):
            mw.undo()
        elif hasattr(mw, 'onUndo'):
            mw.onUndo()
        else:
            logger.debug('Undo method not found')
            return False
        logger.debug('Undo executed')
        return True
    except Exception as e:
        logger.debug('Undo failed: %s', e)
        return False


def _show_answer():
    from aqt import mw

    reviewer = mw.reviewer
    if not reviewer or mw.state != 'review':
        return False

    if reviewer.state == 'question':
        reviewer._showAnswer()
        logger.debug('Showed answer')
        return True
    return False
