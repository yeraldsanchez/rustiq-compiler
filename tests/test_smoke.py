"""Prueba mínima para que CI pase mientras no existan las pruebas reales."""


def test_importa_paquete():
    import rustiq  # noqa: F401
