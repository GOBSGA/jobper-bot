"""
Gestor de base de datos para Jobper Bot v3.0 (Premium)
Provee operaciones CRUD para usuarios, contratos, embeddings y alertas
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from database.models import (
    Contract,
    ContractAddendum,
    ContractApplication,
    ConversationState,
    Country,
    DataSource,
    DeadlineAlert,
    IndustryEmbedding,
    PrivateContract,
    PrivateContractStatus,
    SourceType,
    User,
    UserContract,
    get_session,
    init_database,
)


class DatabaseManager:
    """Gestor de operaciones de base de datos."""

    _instance = None

    def __new__(cls):
        """Singleton para mantener una única instancia del manager."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            init_database()
        return cls._instance

    def get_session(self) -> Session:
        """Obtiene una nueva sesión de base de datos."""
        return get_session()

    # =========================================================================
    # OPERACIONES DE USUARIO
    # =========================================================================

    def get_or_create_user(self, phone: str) -> Tuple[dict, bool]:
        """
        Obtiene un usuario por teléfono o lo crea si no existe.

        Returns:
            tuple: (usuario_dict, es_nuevo)
        """
        session = self.get_session()
        try:
            user = session.query(User).filter(User.phone == phone).first()

            if user:
                user.last_interaction = datetime.utcnow()
                session.commit()
                user_dict = self._user_to_dict(user)
                return user_dict, False

            # Crear nuevo usuario
            user = User(phone=phone, state=ConversationState.NEW.value)
            session.add(user)
            session.commit()
            session.refresh(user)
            user_dict = self._user_to_dict(user)

            return user_dict, True
        finally:
            session.close()

    def get_user_by_phone(self, phone: str) -> Optional[dict]:
        """Obtiene un usuario por su número de teléfono."""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.phone == phone).first()
            if user:
                return self._user_to_dict(user)
            return None
        finally:
            session.close()

    def get_user(self, phone: str) -> Optional[dict]:
        """Alias de get_user_by_phone para compatibilidad con API."""
        return self.get_user_by_phone(phone)

    def get_user_by_id(self, user_id: int) -> Optional[dict]:
        """Obtiene un usuario por su ID."""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if user:
                return self._user_to_dict(user)
            return None
        finally:
            session.close()

    def update_user_state(self, phone: str, state: str) -> Optional[dict]:
        """Actualiza el estado de conversación de un usuario."""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.phone == phone).first()
            if user:
                user.state = state if isinstance(state, str) else state.value
                user.last_interaction = datetime.utcnow()
                session.commit()
                return self._user_to_dict(user)
            return None
        finally:
            session.close()

    def update_user_preferences(
        self,
        phone: str,
        industry: str = None,
        include_keywords: List[str] = None,
        exclude_keywords: List[str] = None,
        countries: str = None,
        min_budget: float = None,
        max_budget: float = None,
    ) -> Optional[dict]:
        """Actualiza las preferencias de un usuario."""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.phone == phone).first()
            if not user:
                return None

            if industry is not None:
                user.industry = industry
            if include_keywords is not None:
                user.include_keywords = include_keywords
            if exclude_keywords is not None:
                user.exclude_keywords = exclude_keywords
            if countries is not None:
                user.countries = countries if isinstance(countries, str) else countries.value
            if min_budget is not None:
                user.min_budget = min_budget
            if max_budget is not None:
                user.max_budget = max_budget

            user.last_interaction = datetime.utcnow()
            session.commit()

            return self._user_to_dict(user)
        finally:
            session.close()

    def update_user(self, phone: str, **kwargs) -> Optional[dict]:
        """Actualiza campos del usuario de forma genérica."""
        return self.update_user_preferences(
            phone,
            industry=kwargs.get("industry"),
            include_keywords=kwargs.get("include_keywords"),
            exclude_keywords=kwargs.get("exclude_keywords"),
            countries=kwargs.get("countries"),
            min_budget=kwargs.get("min_budget"),
            max_budget=kwargs.get("max_budget"),
        )

    def update_user_embedding(self, phone: str, embedding: bytes) -> Optional[dict]:
        """Actualiza el embedding del perfil de un usuario."""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.phone == phone).first()
            if user:
                user.profile_embedding = embedding
                user.embedding_updated_at = datetime.utcnow()
                session.commit()
                return self._user_to_dict(user)
            return None
        finally:
            session.close()

    def set_user_temp_data(self, phone: str, key: str, value) -> Optional[dict]:
        """Guarda datos temporales durante el flujo de registro."""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.phone == phone).first()
            if user:
                temp_data = dict(user.temp_data) if user.temp_data else {}
                temp_data[key] = value
                user.temp_data = temp_data
                session.commit()
                return self._user_to_dict(user)
            return None
        finally:
            session.close()

    def get_user_temp_data(self, phone: str, key: str, default=None):
        """Obtiene datos temporales del usuario."""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.phone == phone).first()
            if user and user.temp_data:
                return user.temp_data.get(key, default)
            return default
        finally:
            session.close()

    def clear_user_temp_data(self, phone: str) -> Optional[dict]:
        """Limpia los datos temporales del usuario."""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.phone == phone).first()
            if user:
                user.temp_data = {}
                session.commit()
                return self._user_to_dict(user)
            return None
        finally:
            session.close()

    def get_active_users(self) -> List[dict]:
        """Obtiene todos los usuarios activos con notificaciones habilitadas."""
        session = self.get_session()
        try:
            users = (
                session.query(User)
                .filter(User.state == ConversationState.ACTIVE.value, User.notifications_enabled == True)
                .all()
            )
            return [self._user_to_dict(u) for u in users]
        finally:
            session.close()

    def get_users_by_country(self, country: str) -> List[dict]:
        """Obtiene usuarios que quieren recibir alertas de un país específico."""
        session = self.get_session()
        try:
            country_val = country if isinstance(country, str) else country.value
            users = (
                session.query(User)
                .filter(
                    User.state == ConversationState.ACTIVE.value,
                    User.notifications_enabled == True,
                    or_(User.countries == country_val, User.countries == Country.ALL.value),
                )
                .all()
            )
            return [self._user_to_dict(u) for u in users]
        finally:
            session.close()

    # =========================================================================
    # OPERACIONES DE CONTRATOS
    # =========================================================================

    def get_or_create_contract(self, external_id: str, **kwargs) -> Tuple[dict, bool]:
        """
        Obtiene un contrato por ID externo o lo crea si no existe.

        Returns:
            tuple: (contrato_dict, es_nuevo)
        """
        session = self.get_session()
        try:
            contract = session.query(Contract).filter(Contract.external_id == external_id).first()

            if contract:
                return self._contract_to_dict(contract), False

            # Convertir enums a valores string si es necesario
            if "country" in kwargs and hasattr(kwargs["country"], "value"):
                kwargs["country"] = kwargs["country"].value
            if "source_type" in kwargs and hasattr(kwargs["source_type"], "value"):
                kwargs["source_type"] = kwargs["source_type"].value

            contract = Contract(external_id=external_id, **kwargs)
            session.add(contract)
            session.commit()
            session.refresh(contract)

            return self._contract_to_dict(contract), True
        finally:
            session.close()

    def get_contract_by_external_id(self, external_id: str) -> Optional[dict]:
        """Obtiene un contrato por su ID externo."""
        session = self.get_session()
        try:
            contract = session.query(Contract).filter(Contract.external_id == external_id).first()
            if contract:
                return self._contract_to_dict(contract)
            return None
        finally:
            session.close()

    def get_contract_by_id(self, contract_id: int) -> Optional[dict]:
        """Obtiene un contrato por su ID interno."""
        session = self.get_session()
        try:
            contract = session.query(Contract).filter(Contract.id == contract_id).first()
            if contract:
                return self._contract_to_dict(contract)
            return None
        finally:
            session.close()

    def get_contract(self, contract_id) -> Optional[dict]:
        """Obtiene un contrato por ID (int) o external_id (str)."""
        if isinstance(contract_id, int):
            return self.get_contract_by_id(contract_id)
        return self.get_contract_by_external_id(str(contract_id))

    def update_contract_embedding(self, contract_id: int, embedding: bytes, model_name: str) -> Optional[dict]:
        """Actualiza el embedding de un contrato."""
        session = self.get_session()
        try:
            contract = session.query(Contract).filter(Contract.id == contract_id).first()
            if contract:
                contract.embedding = embedding
                contract.embedding_model = model_name
                contract.embedding_updated_at = datetime.utcnow()
                session.commit()
                return self._contract_to_dict(contract)
            return None
        finally:
            session.close()

    def get_contracts_without_embedding(self, limit: int = 100) -> List[dict]:
        """Obtiene contratos que no tienen embedding calculado."""
        session = self.get_session()
        try:
            contracts = session.query(Contract).filter(Contract.embedding == None).limit(limit).all()
            return [self._contract_to_dict(c) for c in contracts]
        finally:
            session.close()

    def get_contracts_with_deadline_soon(self, days: int = 3) -> List[dict]:
        """Obtiene contratos con deadline próximo."""
        session = self.get_session()
        try:
            now = datetime.utcnow()
            deadline_limit = now + timedelta(days=days)

            contracts = (
                session.query(Contract)
                .filter(Contract.deadline != None, Contract.deadline >= now, Contract.deadline <= deadline_limit)
                .order_by(Contract.deadline.asc())
                .all()
            )

            return [self._contract_to_dict(c) for c in contracts]
        finally:
            session.close()

    def is_contract_sent_to_user(self, user_id: int, contract_id: int) -> bool:
        """Verifica si un contrato ya fue enviado a un usuario."""
        session = self.get_session()
        try:
            exists = (
                session.query(UserContract)
                .filter(UserContract.user_id == user_id, UserContract.contract_id == contract_id)
                .first()
            )
            return exists is not None
        finally:
            session.close()

    def mark_contract_sent(
        self, user_id: int, contract_id: int, relevance_score: float = 0.0, semantic_score: float = 0.0
    ) -> dict:
        """Marca un contrato como enviado a un usuario."""
        session = self.get_session()
        try:
            user_contract = UserContract(
                user_id=user_id, contract_id=contract_id, relevance_score=relevance_score, semantic_score=semantic_score
            )
            session.add(user_contract)
            session.commit()

            return {
                "id": user_contract.id,
                "user_id": user_id,
                "contract_id": contract_id,
                "relevance_score": relevance_score,
                "semantic_score": semantic_score,
            }
        finally:
            session.close()

    def get_user_contract_history(self, user_id: int, limit: int = 50) -> List[dict]:
        """Obtiene el historial de contratos enviados a un usuario."""
        session = self.get_session()
        try:
            user_contracts = (
                session.query(UserContract)
                .filter(UserContract.user_id == user_id)
                .order_by(UserContract.sent_at.desc())
                .limit(limit)
                .all()
            )

            result = []
            for uc in user_contracts:
                if uc.contract:
                    contract_dict = self._contract_to_dict(uc.contract)
                    contract_dict["relevance_score"] = uc.relevance_score
                    contract_dict["semantic_score"] = uc.semantic_score
                    result.append(contract_dict)
            return result
        finally:
            session.close()

    # =========================================================================
    # OPERACIONES DE EMBEDDINGS DE INDUSTRIA
    # =========================================================================

    def get_or_create_industry_embedding(
        self, industry_key: str, embedding: bytes, keywords_hash: str, model_name: str
    ) -> Tuple[dict, bool]:
        """Obtiene o crea un embedding de industria."""
        session = self.get_session()
        try:
            ind_emb = session.query(IndustryEmbedding).filter(IndustryEmbedding.industry_key == industry_key).first()

            if ind_emb:
                # Actualizar si el hash de keywords cambió
                if ind_emb.keywords_hash != keywords_hash:
                    ind_emb.embedding = embedding
                    ind_emb.keywords_hash = keywords_hash
                    ind_emb.model_name = model_name
                    ind_emb.created_at = datetime.utcnow()
                    session.commit()
                return self._industry_embedding_to_dict(ind_emb), False

            ind_emb = IndustryEmbedding(
                industry_key=industry_key, embedding=embedding, keywords_hash=keywords_hash, model_name=model_name
            )
            session.add(ind_emb)
            session.commit()
            session.refresh(ind_emb)

            return self._industry_embedding_to_dict(ind_emb), True
        finally:
            session.close()

    def get_industry_embedding(self, industry_key: str) -> Optional[dict]:
        """Obtiene el embedding de una industria."""
        session = self.get_session()
        try:
            ind_emb = session.query(IndustryEmbedding).filter(IndustryEmbedding.industry_key == industry_key).first()
            if ind_emb:
                return self._industry_embedding_to_dict(ind_emb)
            return None
        finally:
            session.close()

    def get_all_industry_embeddings(self) -> List[dict]:
        """Obtiene todos los embeddings de industrias."""
        session = self.get_session()
        try:
            embeddings = session.query(IndustryEmbedding).all()
            return [self._industry_embedding_to_dict(e) for e in embeddings]
        finally:
            session.close()

    # =========================================================================
    # OPERACIONES DE ALERTAS DE DEADLINE
    # =========================================================================

    def is_deadline_alert_sent(self, user_id: int, contract_id: int, urgency_level: int) -> bool:
        """Verifica si ya se envió una alerta de deadline."""
        session = self.get_session()
        try:
            exists = (
                session.query(DeadlineAlert)
                .filter(
                    DeadlineAlert.user_id == user_id,
                    DeadlineAlert.contract_id == contract_id,
                    DeadlineAlert.urgency_level == urgency_level,
                )
                .first()
            )
            return exists is not None
        finally:
            session.close()

    def mark_deadline_alert_sent(self, user_id: int, contract_id: int, urgency_level: int) -> dict:
        """Marca una alerta de deadline como enviada."""
        session = self.get_session()
        try:
            alert = DeadlineAlert(user_id=user_id, contract_id=contract_id, urgency_level=urgency_level)
            session.add(alert)
            session.commit()

            return {
                "id": alert.id,
                "user_id": user_id,
                "contract_id": contract_id,
                "urgency_level": urgency_level,
                "sent_at": alert.sent_at,
            }
        finally:
            session.close()

    # =========================================================================
    # OPERACIONES DE DATA SOURCES
    # =========================================================================

    def get_or_create_data_source(
        self, source_key: str, display_name: str, country: str, source_type: str = SourceType.GOVERNMENT.value
    ) -> Tuple[dict, bool]:
        """Obtiene o crea una fuente de datos."""
        session = self.get_session()
        try:
            source = session.query(DataSource).filter(DataSource.source_key == source_key).first()

            if source:
                return self._data_source_to_dict(source), False

            source = DataSource(
                source_key=source_key, display_name=display_name, country=country, source_type=source_type
            )
            session.add(source)
            session.commit()
            session.refresh(source)

            return self._data_source_to_dict(source), True
        finally:
            session.close()

    def update_data_source_status(self, source_key: str, success: bool = True) -> Optional[dict]:
        """Actualiza el estado de una fuente de datos después de un fetch."""
        session = self.get_session()
        try:
            source = session.query(DataSource).filter(DataSource.source_key == source_key).first()
            if source:
                if success:
                    source.last_successful_fetch = datetime.utcnow()
                    source.error_count = 0
                else:
                    source.error_count = (source.error_count or 0) + 1
                session.commit()
                return self._data_source_to_dict(source)
            return None
        finally:
            session.close()

    def get_enabled_data_sources(self) -> List[dict]:
        """Obtiene todas las fuentes de datos habilitadas."""
        session = self.get_session()
        try:
            sources = session.query(DataSource).filter(DataSource.is_enabled == True).all()
            return [self._data_source_to_dict(s) for s in sources]
        finally:
            session.close()

    # =========================================================================
    # ESTADÍSTICAS
    # =========================================================================

    def get_stats(self) -> dict:
        """Obtiene estadísticas generales del bot."""
        session = self.get_session()
        try:
            total_users = session.query(User).count()
            active_users = session.query(User).filter(User.state == ConversationState.ACTIVE.value).count()
            total_contracts = session.query(Contract).count()
            total_sent = session.query(UserContract).count()
            contracts_with_embedding = session.query(Contract).filter(Contract.embedding != None).count()

            return {
                "total_users": total_users,
                "active_users": active_users,
                "total_contracts": total_contracts,
                "contracts_with_embedding": contracts_with_embedding,
                "total_notifications_sent": total_sent,
            }
        finally:
            session.close()

    # =========================================================================
    # HELPERS - Convertir modelos a diccionarios
    # =========================================================================

    def _user_to_dict(self, user: User) -> dict:
        """Convierte un modelo User a diccionario."""
        return {
            "id": user.id,
            "phone": user.phone,
            "name": user.name,
            "state": user.state,
            "industry": user.industry,
            "include_keywords": user.include_keywords or [],
            "exclude_keywords": user.exclude_keywords or [],
            "countries": user.countries,
            "min_budget": user.min_budget,
            "max_budget": user.max_budget,
            "notifications_enabled": user.notifications_enabled,
            "notification_frequency": user.notification_frequency,
            "has_embedding": user.profile_embedding is not None,
            "embedding_updated_at": user.embedding_updated_at,
            "temp_data": user.temp_data or {},
            "created_at": user.created_at,
            "updated_at": user.updated_at,
            "last_interaction": user.last_interaction,
        }

    def _contract_to_dict(self, contract: Contract) -> dict:
        """Convierte un modelo Contract a diccionario."""
        return {
            "id": contract.id,
            "external_id": contract.external_id,
            "title": contract.title,
            "description": contract.description,
            "entity": contract.entity,
            "amount": contract.amount,
            "currency": contract.currency,
            "country": contract.country,
            "source": contract.source,
            "source_type": contract.source_type,
            "url": contract.url,
            "publication_date": contract.publication_date,
            "deadline": contract.deadline,
            "has_embedding": contract.embedding is not None,
            "embedding_model": contract.embedding_model,
            "created_at": contract.created_at,
        }

    def _industry_embedding_to_dict(self, ind_emb: IndustryEmbedding) -> dict:
        """Convierte un modelo IndustryEmbedding a diccionario."""
        return {
            "id": ind_emb.id,
            "industry_key": ind_emb.industry_key,
            "embedding": ind_emb.embedding,  # bytes
            "keywords_hash": ind_emb.keywords_hash,
            "model_name": ind_emb.model_name,
            "created_at": ind_emb.created_at,
        }

    def _data_source_to_dict(self, source: DataSource) -> dict:
        """Convierte un modelo DataSource a diccionario."""
        return {
            "id": source.id,
            "source_key": source.source_key,
            "display_name": source.display_name,
            "country": source.country,
            "source_type": source.source_type,
            "is_enabled": source.is_enabled,
            "last_successful_fetch": source.last_successful_fetch,
            "error_count": source.error_count,
            "config": source.config or {},
            "created_at": source.created_at,
        }

    # =========================================================================
    # OPERACIONES DE CONTRATOS PRIVADOS (MARKETPLACE)
    # =========================================================================

    def update_user_temp_data(self, phone: str, data: dict) -> Optional[dict]:
        """Actualiza datos temporales del usuario (merge con existentes)."""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.phone == phone).first()
            if user:
                temp_data = dict(user.temp_data) if user.temp_data else {}
                temp_data.update(data)
                user.temp_data = temp_data
                session.commit()
                return self._user_to_dict(user)
            return None
        finally:
            session.close()

    def create_private_contract(
        self,
        publisher_phone: str,
        title: str,
        description: str = None,
        category: str = None,
        budget_min: float = None,
        budget_max: float = None,
        deadline: datetime = None,
        city: str = None,
        is_remote: bool = False,
        country: str = "colombia",
    ) -> Optional[int]:
        """
        Crea un nuevo contrato privado en el marketplace.

        Returns:
            ID del contrato creado o None si falla
        """
        session = self.get_session()
        try:
            # Obtener usuario
            user = session.query(User).filter(User.phone == publisher_phone).first()
            if not user:
                return None

            contract = PrivateContract(
                publisher_id=user.id,
                title=title,
                description=description,
                category=category,
                budget_min=budget_min,
                budget_max=budget_max,
                deadline=deadline,
                city=city,
                is_remote=is_remote,
                country=country,
                status=PrivateContractStatus.ACTIVE.value,
            )
            session.add(contract)
            session.commit()
            session.refresh(contract)

            return contract.id
        finally:
            session.close()

    def get_private_contract(self, contract_id: int) -> Optional[dict]:
        """Obtiene un contrato privado por ID."""
        session = self.get_session()
        try:
            contract = session.query(PrivateContract).filter(PrivateContract.id == contract_id).first()
            if contract:
                return self._private_contract_to_dict(contract)
            return None
        finally:
            session.close()

    def get_user_private_contracts(self, phone: str, status: str = None) -> List[dict]:
        """Obtiene los contratos privados publicados por un usuario."""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.phone == phone).first()
            if not user:
                return []

            query = session.query(PrivateContract).filter(PrivateContract.publisher_id == user.id)

            if status:
                query = query.filter(PrivateContract.status == status)

            contracts = query.order_by(PrivateContract.created_at.desc()).all()
            return [self._private_contract_to_dict(c) for c in contracts]
        finally:
            session.close()

    def get_active_private_contracts(self, category: str = None, country: str = None, limit: int = 50) -> List[dict]:
        """Obtiene contratos privados activos para mostrar a contratistas."""
        session = self.get_session()
        try:
            query = session.query(PrivateContract).filter(PrivateContract.status == PrivateContractStatus.ACTIVE.value)

            if category:
                query = query.filter(PrivateContract.category == category)
            if country:
                query = query.filter(PrivateContract.country == country)

            contracts = query.order_by(PrivateContract.created_at.desc()).limit(limit).all()

            return [self._private_contract_to_dict(c) for c in contracts]
        finally:
            session.close()

    def update_private_contract_status(self, contract_id: int, status: str) -> Optional[dict]:
        """Actualiza el estado de un contrato privado."""
        session = self.get_session()
        try:
            contract = session.query(PrivateContract).filter(PrivateContract.id == contract_id).first()
            if contract:
                contract.status = status
                session.commit()
                return self._private_contract_to_dict(contract)
            return None
        finally:
            session.close()

    def create_contract_application(
        self,
        contract_id: int,
        applicant_phone: str,
        proposed_amount: float = None,
        message: str = None,
        estimated_days: int = None,
        match_score: float = 0.0,
    ) -> Optional[int]:
        """
        Crea una aplicación/propuesta para un contrato privado.

        Returns:
            ID de la aplicación o None si falla
        """
        session = self.get_session()
        try:
            # Obtener usuario
            user = session.query(User).filter(User.phone == applicant_phone).first()
            if not user:
                return None

            # Verificar que no haya aplicado antes
            existing = (
                session.query(ContractApplication)
                .filter(ContractApplication.contract_id == contract_id, ContractApplication.applicant_id == user.id)
                .first()
            )
            if existing:
                return existing.id  # Ya aplicó

            application = ContractApplication(
                contract_id=contract_id,
                applicant_id=user.id,
                proposed_amount=proposed_amount,
                message=message,
                estimated_days=estimated_days,
                match_score=match_score,
            )
            session.add(application)
            session.commit()
            session.refresh(application)

            return application.id
        finally:
            session.close()

    def get_contract_applications(self, contract_id: int) -> List[dict]:
        """Obtiene todas las aplicaciones para un contrato privado."""
        session = self.get_session()
        try:
            applications = (
                session.query(ContractApplication)
                .filter(ContractApplication.contract_id == contract_id)
                .order_by(ContractApplication.match_score.desc())
                .all()
            )

            return [self._application_to_dict(a) for a in applications]
        finally:
            session.close()

    def get_users_by_category(self, category: str, country: str = None, limit: int = 100) -> List[dict]:
        """
        Obtiene usuarios que podrían estar interesados en una categoría.
        Busca por industria y keywords relacionadas.
        """
        session = self.get_session()
        try:
            query = session.query(User).filter(
                User.state == ConversationState.ACTIVE.value, User.notifications_enabled == True
            )

            if country:
                query = query.filter(or_(User.countries == country, User.countries == "all"))

            users = query.limit(limit).all()

            # Filtrar por categoría/industria relevante
            category_industry_map = {
                "tecnologia": ["tecnologia", "software"],
                "construccion": ["construccion", "ingenieria"],
                "consultoria": ["consultoria", "legal"],
                "diseño": ["publicidad", "marketing"],
            }

            related_industries = category_industry_map.get(category, [category])

            relevant_users = []
            for user in users:
                # Verificar industria
                if user.industry in related_industries:
                    relevant_users.append(self._user_to_dict(user))
                    continue

                # Verificar keywords
                keywords = user.include_keywords or []
                if any(category in kw.lower() for kw in keywords):
                    relevant_users.append(self._user_to_dict(user))

            return relevant_users
        finally:
            session.close()

    def _private_contract_to_dict(self, contract: PrivateContract) -> dict:
        """Convierte un modelo PrivateContract a diccionario."""
        return {
            "id": contract.id,
            "publisher_id": contract.publisher_id,
            "title": contract.title,
            "description": contract.description,
            "category": contract.category,
            "budget_min": contract.budget_min,
            "budget_max": contract.budget_max,
            "currency": contract.currency,
            "city": contract.city,
            "country": contract.country,
            "is_remote": contract.is_remote,
            "deadline": contract.deadline,
            "status": contract.status,
            "keywords": contract.keywords or [],
            "selected_contractor_id": contract.selected_contractor_id,
            "created_at": contract.created_at,
            "updated_at": contract.updated_at,
        }

    def _application_to_dict(self, app: ContractApplication) -> dict:
        """Convierte un modelo ContractApplication a diccionario."""
        return {
            "id": app.id,
            "contract_id": app.contract_id,
            "applicant_id": app.applicant_id,
            "proposed_amount": app.proposed_amount,
            "message": app.message,
            "estimated_days": app.estimated_days,
            "status": app.status,
            "match_score": app.match_score,
            "applied_at": app.applied_at,
            "responded_at": app.responded_at,
        }
