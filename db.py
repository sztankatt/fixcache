from sqlalchemy import Column, Integer, Boolean, DateTime
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class Commit(Base):
    __tablename__ = 'commits'

    id = Column(Integer, primary_key=True)
    pushed_time = Column(DateTime)
    is_fix = Column(Boolean)


class DB():
    def __init__(self, eng):
        self.engine = create_engine(eng)

    def setup(self):
        Base.metadata.create_all(self.engine)
        DBSession = sessionmaker(bind=self.engine)
        self.session = DBSession()
        return self.session

    def teardown(self):
        self.session.close()
        Base.metadata.drop_all(self.engine)
