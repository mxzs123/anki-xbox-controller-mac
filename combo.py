import logging

logger = logging.getLogger(__name__)

COMBO_ACTIONS = {'answer_2', 'answer_3', 'answer_4'}
BREAK_ACTIONS = {'answer_1'}


class ComboTracker:
    def __init__(self):
        self.streak = 0
        self.best_streak = 0
        self.total_reviewed = 0
        self.enabled = True
        self.milestone_interval = 25
        self.streak_thresholds = [5, 10, 20]

    def feed(self, action_name):
        if not self.enabled:
            return None

        if action_name in COMBO_ACTIONS:
            self.streak += 1
            self.total_reviewed += 1
            if self.streak > self.best_streak:
                self.best_streak = self.streak
            return self._evaluate()

        if action_name in BREAK_ACTIONS:
            old_streak = self.streak
            self.streak = 0
            self.total_reviewed += 1
            if old_streak >= self.streak_thresholds[0]:
                return {'event': 'combo_break', 'lost_streak': old_streak}
            return {'event': 'fail'}

        return None

    def _evaluate(self):
        result = {'event': 'answer', 'streak': self.streak}

        if self.total_reviewed > 0 and self.total_reviewed % self.milestone_interval == 0:
            result['milestone'] = self.total_reviewed

        thresholds = sorted(self.streak_thresholds)
        if self.streak >= thresholds[-1]:
            result['tier'] = 3
        elif len(thresholds) >= 2 and self.streak >= thresholds[-2]:
            result['tier'] = 2
        elif self.streak >= thresholds[0]:
            result['tier'] = 1
        else:
            result['tier'] = 0

        if self.streak in self.streak_thresholds:
            result['threshold_hit'] = True

        return result

    def reset(self):
        self.streak = 0
        self.best_streak = 0
        self.total_reviewed = 0
