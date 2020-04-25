import dataset
from dynaconf import settings
from fexservice.exception import ConsumerCritical, ConsumerWarning
from fexservice.logger import logger
from fexservice.validator import validators
from github import Github

# Fire the validator settings
settings.validators.register(*validators)
settings.validators.validate()

try:
    github = Github(settings.GITHUB_TOKEN)
except AttributeError as e:
    logger.critical(e)
    exit(1)

# TODO: ConnectionError
db = dataset.connect(settings.DATABASE_URL, engine_kwargs={"echo": True})
repo = db["repos"]


def fetch_github():
    """Fetches Github api and stores in database."""
    try:
        repositories = github.search_repositories(
            query=settings.SEARCH_QUERY, sort="stars"
        )
        if 0 == repositories.totalCount:
            logger.critical("Bad SEARCH_QUERY")
            exit(1)
        for item in repositories:
            data = dict(
                id=item.id,
                name=item.name,
                full_name=item.full_name,
                html_url=item.html_url,
                description=item.description,
                created_at=item.created_at,
                updated_at=item.updated_at,
                stargazers_count=item.stargazers_count,
                forks_count=item.forks_count,
            )
            repo.upsert(data, ["id"])
    # Erros de Internet
    except ConsumerWarning as e:
        logger.warning(e)
    except ConsumerCritical as e:
        # Erro na configuração
        logger.critical(e)
        exit(1)
