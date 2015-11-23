from sqlalchemy import Column, Integer, Boolean, \
    DateTime, Table, ForeignKey, String, Enum
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.hybrid import hybrid_property

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
    distance1 = relationship(
        "FileDistance",
        backref="file1",
        primaryjoin="and_(File.id==FileDistance.file1_id)")
    distance2 = relationship(
        "FileDistance",
        backref="file2",
        primaryjoin="and_(File.id==FileDistance.file2_id)")


class Change(Base):
    __tablename__ = 'change'

    id = Column(Integer, primary_key=True)
    change_type = Column(
        Enum('creation', 'deletion', 'change', name='change_type'))
    file_id = Column(Integer, ForeignKey('file.id'))
    commit_id = Column(Integer, ForeignKey('commit.id'))
    file = relationship("File", backref='change')
    commit = relationship("Commit", backref='change')


class FileDistance(Base):
    __tablename__ = 'file_distance'
    id = Column(Integer, primary_key=True)
    file1_id = Column(Integer, ForeignKey('file.id'))
    file2_id = Column(Integer, ForeignKey('file.id'))
    change_num = Column(Integer)

    @hybrid_property
    def distance(self):
        return 1/float(self.change_num)


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
