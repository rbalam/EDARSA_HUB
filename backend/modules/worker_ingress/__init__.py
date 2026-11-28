"""Remote canonical ingress for the EDARSAHUB Universal Worker."""

__all__ = ["router"]


def __getattr__(name):
    if name == "router":
        from .routes import router
        return router
    raise AttributeError(name)
