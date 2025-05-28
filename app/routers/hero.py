from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlmodel import Session, select
from typing import List, Optional

from app.models.hero import Hero
from app.schemas.hero import HeroCreate, HeroRead, HeroUpdate
from app.db.database import engine

router = APIRouter()


def get_session():
    with Session(engine) as session:
        yield session


@router.post("/heroes/", response_model=HeroRead)
def create_hero(hero: HeroCreate, session: Session = Depends(get_session)):
    new_hero = Hero(**hero.model_dump())
    session.add(new_hero)
    session.commit()
    session.refresh(new_hero)
    return new_hero


@router.get("/heroes/", response_model=List[HeroRead])
def get_heros(
    min_age: Optional[int] = None,
    max_age: Optional[int] = None,
    search: Optional[str] = None,
    sort_by: Optional[str] = Query(default="id", pattern="^(id|name|age)$"),
    sort_order: Optional[str] = Query(default="asc", pattern="^(asc|desc)$"),
    session: Session = Depends(get_session),
):
    statement = select(Hero)

    if min_age is not None:
        statement = statement.where(Hero.age >= min_age)
    if max_age is not None:
        statement = statement.where(Hero.age <= max_age)
    if search:
        statement = statement.where(Hero.name.contains(search))

    # Handle sorting
    sort_column = getattr(Hero, sort_by)
    if sort_order == "desc":
        sort_column = sort_column.desc()
    statement = statement.order_by(sort_column)

    results = session.exec(statement)
    heroes = results.all()
    return heroes


@router.get("/heroes/{hero_id}", response_model=HeroRead)
def get_hero_by_id(hero_id: int, session: Session = Depends(get_session)):
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    return hero


@router.put("/heroes/{hero_id}", response_model=HeroRead)
def update_hero(
    hero_id: int,
    updated_hero: HeroCreate,
    session: Session = Depends(get_session),
):
    existing_hero = session.get(Hero, hero_id)

    if not existing_hero:
        raise HTTPException(status_code=404, detail="Hero not found")

    existing_hero.name = updated_hero.name
    existing_hero.secret_name = updated_hero.secret_name
    existing_hero.age = updated_hero.age

    session.add(existing_hero)
    session.commit()
    session.refresh(existing_hero)

    return existing_hero


@router.patch("/heroes/{hero_id}", response_model=HeroRead)
def patch_hero(
    hero_id: int,
    hero_update: HeroUpdate,
    session: Session = Depends(get_session)
):
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    
    hero_data = hero_update.model_dump(exclude_unset=True)
    
    for key, value in hero_data.items():
        setattr(hero, key, value)
        
    session.add(hero)
    session.commit()
    session.refresh(hero)
    
    return hero

@router.delete("/heroes/{hero_id}")
def delete_hero(
    hero_id: int,
    session: Session = Depends(get_session)
):
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    
    session.delete(hero)
    session.commit()
    return None