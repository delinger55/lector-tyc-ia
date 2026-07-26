"""Tests para el frontend (template HTML renderizado por GET /).

Verifica que el HTML contiene los elementos requeridos:
- Disclaimer legal en estado upload y results
- Input file con accept .pdf,.docx
- 3 secciones de estado
- Botón analizar
- Aviso de envío a API externa
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    """Cliente HTTP para tests del frontend."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestFrontendHTML:
    """Tests para verificar contenido del HTML renderizado."""

    async def test_contains_disclaimer_text(self, client: AsyncClient):
        """HTML contiene el texto del disclaimer legal."""
        response = await client.get("/")
        assert response.status_code == 200
        html = response.text
        assert "inteligencia artificial" in html
        assert "fines informativos" in html
        assert "no constituye asesoría legal profesional" in html

    async def test_contains_file_input(self, client: AsyncClient):
        """HTML contiene input type=file con accept .pdf,.docx."""
        response = await client.get("/")
        html = response.text
        assert 'type="file"' in html
        assert 'accept=".pdf,.docx"' in html

    async def test_contains_three_state_sections(self, client: AsyncClient):
        """HTML contiene las 3 secciones de estado."""
        response = await client.get("/")
        html = response.text
        assert 'id="state-upload"' in html
        assert 'id="state-processing"' in html
        assert 'id="state-results"' in html

    async def test_contains_analyze_button(self, client: AsyncClient):
        """HTML contiene el botón 'Analizar documento'."""
        response = await client.get("/")
        html = response.text
        assert "Analizar documento" in html

    async def test_contains_api_external_notice(self, client: AsyncClient):
        """HTML contiene aviso de que el contenido se envía a API externa."""
        response = await client.get("/")
        html = response.text
        assert "API externa" in html

    async def test_contains_new_analysis_button(self, client: AsyncClient):
        """HTML contiene botón para analizar otro documento."""
        response = await client.get("/")
        html = response.text
        assert "Analizar otro documento" in html

    async def test_processing_state_is_hidden(self, client: AsyncClient):
        """El estado processing está oculto inicialmente (class hidden)."""
        response = await client.get("/")
        html = response.text
        # state-processing debe tener class hidden
        assert 'id="state-processing" class="state-section hidden"' in html

    async def test_results_state_is_hidden(self, client: AsyncClient):
        """El estado results está oculto inicialmente (class hidden)."""
        response = await client.get("/")
        html = response.text
        assert 'id="state-results" class="state-section hidden"' in html

    async def test_upload_state_is_visible(self, client: AsyncClient):
        """El estado upload está visible inicialmente (sin class hidden)."""
        response = await client.get("/")
        html = response.text
        # state-upload NO tiene hidden
        assert 'id="state-upload" class="state-section"' in html

    async def test_contains_drag_and_drop_zone(self, client: AsyncClient):
        """HTML contiene la zona de drag-and-drop."""
        response = await client.get("/")
        html = response.text
        assert 'id="drop-zone"' in html
        assert "Arrastra" in html

    async def test_contains_severity_legend(self, client: AsyncClient):
        """HTML contiene la leyenda de niveles de riesgo."""
        response = await client.get("/")
        html = response.text
        assert "Niveles de riesgo" in html
        assert "legend-item--high" in html
        assert "legend-item--medium" in html
        assert "legend-item--low" in html

    async def test_disclaimer_in_results_section(self, client: AsyncClient):
        """HTML contiene disclaimer dentro de la sección de resultados."""
        response = await client.get("/")
        html = response.text
        # El disclaimer compacto está en results-sidebar
        assert "disclaimer--compact" in html

    async def test_loads_css_and_js(self, client: AsyncClient):
        """HTML referencia los archivos CSS y JS correctamente."""
        response = await client.get("/")
        html = response.text
        assert '/static/css/styles.css' in html
        assert '/static/js/app.js' in html
