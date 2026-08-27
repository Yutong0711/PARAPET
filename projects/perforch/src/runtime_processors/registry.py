from . import cpp_processor
from . import go_processor
from . import java_processor
from . import python_processor
from . import rust_processor


_PROCESSORS = {
    "cpp": cpp_processor,
    "rust": rust_processor,
    "go": go_processor,
    "python": python_processor,
    "java": java_processor,
}

SUPPORTED_LANGUAGES = tuple(_PROCESSORS.keys())


def get_processor(language: str):
    language_key = language.lower()
    if language_key not in _PROCESSORS:
        raise ValueError(f"Unsupported language: {language}")
    return _PROCESSORS[language_key]
