from sqlalchemy import Column, Integer, Boolean, \
    DateTime, Table, ForeignKey, String, Enum
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

Base = declarative_base()


class Commit(Base):
    __tablename__ = 'commit'

    id = Column(Integer, primary_key=True)
    pushed_time = Column(DateTime)
    is_fix = Column(Boolean)


class File(Base):
    __tablename__ = 'file'

    id = Column(Integer, primary_key=True)
    path = Column(String, unique=True)


class Change(Base):
    __tablename__ = 'change'

    id = Column(Integer, primary_key=True)
    change_type = Column(
        Enum('creation', 'deletion', 'change', name='change_type'))
    file_id = Column(Integer, ForeignKey('file.id'))
    commit_id = Column(Integer, ForeignKey('commit.id'))
    file = relationship("File", backref='change')
    commit = relationship("Commit", backref='change')

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
