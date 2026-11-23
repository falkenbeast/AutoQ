import logging
from typing import List, Optional, Tuple, Union
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.exceptions import EntityNotFoundException, ValidationException
from app.models.component import Component
from app.schemas.component import ComponentCreate, ComponentUpdate

logger = logging.getLogger("autoq.services.component")


class ComponentService:
    """Service layer managing automotive component catalog entities."""

    def get_components(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 50,
        category: Optional[str] = None,
    ) -> Tuple[List[Component], int]:
        """Retrieves paginated components with optional category filter."""
        query = db.query(Component)
        if category:
            query = query.filter(func.lower(Component.component_category) == category.strip().lower())
        
        total = query.count()
        items = query.order_by(Component.component_id.asc()).offset(skip).limit(limit).all()
        return items, total

    def get_component_by_id(
        self,
        db: Session,
        id_or_code: Union[int, str],
    ) -> Component:
        """Retrieves a component by numeric primary key or unique component code."""
        if isinstance(id_or_code, int) or (isinstance(id_or_code, str) and id_or_code.isdigit()):
            comp = db.query(Component).filter(Component.id == int(id_or_code)).first()
            if comp:
                return comp

        comp = db.query(Component).filter(Component.component_id == str(id_or_code).strip().upper()).first()
        if not comp:
            raise EntityNotFoundException("Component", id_or_code)
        return comp

    def create_component(
        self,
        db: Session,
        payload: ComponentCreate,
    ) -> Component:
        """Creates a new automotive component entity."""
        existing = db.query(Component).filter(Component.component_id == payload.component_id).first()
        if existing:
            raise ValidationException(
                f"Component with ID '{payload.component_id}' already exists in catalog.",
                field="component_id",
            )

        component = Component(
            component_id=payload.component_id,
            component_name=payload.component_name,
            component_category=payload.component_category,
            description=payload.description,
        )
        db.add(component)
        db.commit()
        db.refresh(component)
        logger.info(f"Created component: {component.component_id} ({component.component_name})")
        return component

    def get_or_create_component(
        self,
        db: Session,
        component_id: str,
        component_name: str,
        component_category: str,
    ) -> Component:
        """Retrieves component if exists; otherwise creates a new record automatically."""
        clean_id = component_id.strip().upper()
        comp = db.query(Component).filter(Component.component_id == clean_id).first()
        if not comp:
            comp = Component(
                component_id=clean_id,
                component_name=component_name.strip(),
                component_category=component_category.strip(),
                description=f"Auto-cataloged via inspection of {component_name.strip()}",
            )
            db.add(comp)
            db.flush()
            logger.info(f"Auto-cataloged new component: {comp.component_id}")
        return comp

    def update_component(
        self,
        db: Session,
        id_or_code: Union[int, str],
        payload: ComponentUpdate,
    ) -> Component:
        """Updates component attributes."""
        component = self.get_component_by_id(db, id_or_code)
        update_data = payload.model_dump(exclude_unset=True)

        for key, val in update_data.items():
            if val is not None:
                setattr(component, key, val)

        db.commit()
        db.refresh(component)
        logger.info(f"Updated component: {component.component_id}")
        return component


component_service = ComponentService()

