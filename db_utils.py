from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError

def get_one_or_create(session,
                      model,
                      create_method='',
                      create_method_kwargs=None,
                      **kwargs):
    try:
        return session.query(model).filter_by(**kwargs).one(), True
    except NoResultFound:
        kwargs.update(create_method_kwargs or {})
        try:
            with session.begin_nested():
                created = getattr(model, create_method, model)(**kwargs)
                session.add(created)
            return created, False
        except IntegrityError:
            return session.query(model).filter_by(**kwargs).one(), True