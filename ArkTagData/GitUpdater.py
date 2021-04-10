import os
from utils.logger import Logger


def updateGameData(path="./ArknightsGameData"):
    logger = Logger.get()
    try:
        import git
    except (ImportError, ModuleNotFoundError) as e:
        logger.error("Cannot find git, try \"pip install gitpython\" instead")
        return False

    repo = git.Repo(os.path.abspath(path))
    logger.system("current branch:" + str(repo.active_branch))
    for output in repo.remote().pull():
        logger.system(str(output))
    logger.system("ArknightsGameData update successfully")
    return True
