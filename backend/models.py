from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum, Date, Float
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import enum

Base = declarative_base()


#The following are the roles that users can have, if i missed a role please add it. The admin will be managed differently later
class RoleEnum(str, enum.Enum):
    centra = "centra"
    xyz = "xyz"
    GuardHarbor = "GuardHarbor"


class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(length=500), nullable=False)
    email = Column(String(length=500), unique=True, nullable=False)
    hashed_password = Column(String(length=500), nullable=False)
    role = Column(SQLEnum(RoleEnum), default=RoleEnum.centra, nullable=False)
    refresh_tokens = relationship(
        "RefreshToken", back_populates="user", order_by="RefreshToken.expires_at.desc()")
    
#the user will choose their role during registration so the role field can be part of the Users table and no need for a Role table

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(length=7000), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    expires_at = Column(DateTime, nullable=False)

    user = relationship("Users", back_populates="refresh_tokens")


# Centra, etc


class Appointment(Base):
    __tablename__ = "appointment"

    id = Column(Integer, primary_key=True, index=True)
    shipping_id = Column(Integer, ForeignKey("shipping.id"))
    receiver_name = Column(String)
    pickup_time = Column(Date)

    shipping = relationship("Shipping", backref="appointment")


class Centra(Base):
    __tablename__ = "centra"

    id = Column(Integer, primary_key=True, index=True)
    location = Column(String)
    collection_id = Column(Integer, ForeignKey("collection.id"))
    package_data_id = Column(Integer, ForeignKey("package_data.id"))
    reception_package_id = Column(Integer, ForeignKey("reception_package.id"))

    collection_centra = relationship("Collection", backref="centra")
    package_data_centra = relationship("PackageData", backref="centra")
    reception_package_centra = relationship(
        "ReceptionPackage", backref="centra")


class CheckpointData(Base):
    __tablename__ = "checkpoint_data"

    id = Column(Integer, primary_key=True, index=True)
    arrival_date = Column(Date)
    total_weight = Column(Float)
    total_packages = Column(Integer)
    shipping_id = Column(Integer, ForeignKey("shipping.id"))

    shipping = relationship("Shipping", backref="shipping_collection")


class Expedition(Base):
    __tablename__ = "expedition"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)


class PackageData(Base):
    __tablename__ = "package_data"

    id = Column(Integer, primary_key=True, index=True)
    shipping_collection_id = Column(Integer)
    centra_id = Column(Integer, ForeignKey("centra.id"))
    weight = Column(Float)

    centra_owner = relationship("Centra", backref="package_data")


class RescaledPackageData(Base):
    __tablename__ = "rescaled_package_data"

    id = Column(Integer, primary_key=True, index=True)
    package_id = Column(Integer, ForeignKey("package_data.id"))
    rescaled_weight = Column(Float)

    original_package = relationship(
        "PackageData", backref="rescaled_package_data")


class ReceptionPackage(Base):
    __tablename__ = "reception_package"

    id = Column(Integer, primary_key=True, index=True)
    package_id = Column(Integer, ForeignKey("package_data.id"))
    final_weight = Column(Float)
    receival_date = Column(Date)
    centra_id = Column(Integer, ForeignKey("centra.id"))

    source_centra = relationship("Centra", backref="reception_package")
    original_package = relationship("PackageData", backref="reception_package")


class Shipping(Base):
    __tablename__ = "shipping"

    id = Column(Integer, primary_key=True, index=True)
    departure_date = Column(Date)
    expedition_id = Column(Integer, ForeignKey("expedition.id"))
    guard_harbor_dest_id = Column(Integer, ForeignKey("guard_harbor.id"))

    expedition = relationship("Expedition", backref="shipping")
    guard_harbor = relationship("GuardHarbor", backref="shipping")


class GuardHarbor(Base):
    __tablename__ = "guard_harbor"

    id = Column(Integer, primary_key=True, index=True)
    location = Column(String)
    checkpoint_id = Column(Integer, ForeignKey("checkpoint_data.id"))

    checkpoint = relationship("CheckpointData", backref="guard_harbor")


class Collection(Base):
    __tablename__ = "collection"

    id = Column(Integer, primary_key=True, index=True)
    retrieval_date = Column(Date)
    weight = Column(Float)
    centra_id = Column(Integer, ForeignKey("centra.id"))

    centra = relationship("Centra", backref="collection")


class Dry(Base):
    __tablename__ = "dry"

    id = Column(Integer, primary_key=True, index=True)
    weight = Column(Float)
    exp_date = Column(Date)


class Flour(Base):
    __tablename__ = "flour"

    id = Column(Integer, primary_key=True, index=True)
    weight = Column(Float)
    finish_time = Column(Date)