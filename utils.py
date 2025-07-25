# utils.py

def print_login_required():
    print("User not logged in. Please log in to your DAB account to use DABCLI.\n"
          "Run: dabcli.py login <email> <password>")


def is_logged_in(config):
    return bool(config.token)


def require_login(config, silent=False):
    if not is_logged_in(config):
        if not silent:
            print_login_required()
        return False
    return True