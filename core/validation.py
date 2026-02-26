import re

class Validator:
    _format_pattern = re.compile(r'^[a-zA-Z0-9._-]+$')
    _pinterest_pattern = re.compile(r'^[a-zA-Z0-9_]+$')
    _github_pattern = re.compile(r'^[a-zA-Z0-9-]+$')
    _instagram_pattern = re.compile(r'^[a-zA-Z0-9._]+$')
    _consecutive_dots = re.compile(r'\.\.')
    
    @staticmethod
    def validate_format(username):
        if not username: return False
        if not Validator._format_pattern.match(username): return False
        return True

    @staticmethod
    def check_pinterest(username):
        if len(username) < 3 or len(username) > 30: return False
        if not Validator._pinterest_pattern.match(username): return False
        if username.isdigit(): return False
        return True

    @staticmethod
    def check_github(username):
        if len(username) > 39: return False
        if username.startswith('-') or username.endswith('-'): return False
        if '--' in username: return False
        if not Validator._github_pattern.match(username): return False
        return True

    @staticmethod
    def check_instagram(username):
        if len(username) > 30: return False
        if username.startswith('.') or username.endswith('.'): return False
        if Validator._consecutive_dots.search(username): return False
        if not Validator._instagram_pattern.match(username): return False
        return True
