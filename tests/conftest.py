"""
Pytest configuration and fixtures for Jobper tests
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

# Agregar el directorio raíz al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))


@pytest.fixture
def sample_contract_data():
    """Fixture con datos de contrato de ejemplo."""
    from scrapers.base import ContractData

    return ContractData(
        external_id="TEST-001",
        title="Desarrollo de Software de Gestión Empresarial",
        description="Contrato para el desarrollo de un sistema de gestión empresarial con módulos de inventario, facturación y recursos humanos.",
        entity="Ministerio de Tecnología",
        amount=500_000_000,
        currency="COP",
        country="colombia",
        source="SECOP II",
        url="https://example.com/contract/TEST-001",
        publication_date=datetime.now() - timedelta(days=2),
        deadline=datetime.now() + timedelta(days=5),
        raw_data={},
    )


@pytest.fixture
def sample_contracts_list(sample_contract_data):
    """Fixture con lista de contratos de ejemplo."""
    from scrapers.base import ContractData

    contracts = [sample_contract_data]

    contracts.append(
        ContractData(
            external_id="TEST-002",
            title="Suministro de equipos de cómputo",
            description="Adquisición de computadores portátiles y de escritorio para uso institucional.",
            entity="Alcaldía de Bogotá",
            amount=200_000_000,
            currency="COP",
            country="colombia",
            source="SECOP II",
            url="https://example.com/contract/TEST-002",
            publication_date=datetime.now() - timedelta(days=1),
            deadline=datetime.now() + timedelta(days=2),
            raw_data={},
        )
    )

    contracts.append(
        ContractData(
            external_id="TEST-003",
            title="IT Consulting Services",
            description="Professional consulting services for IT infrastructure modernization.",
            entity="Department of Defense",
            amount=500_000,
            currency="USD",
            country="usa",
            source="SAM.gov",
            url="https://sam.gov/opp/TEST-003/view",
            publication_date=datetime.now() - timedelta(days=3),
            deadline=datetime.now() + timedelta(days=10),
            raw_data={},
        )
    )

    return contracts
