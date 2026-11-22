"""Simple test module for SpectraCam-AIO."""


def register(app):
    @app.get("/modules/test")
    def test():
        return {"module": "test", "status": "ok"}
