"""Open Response available editors configuration"""

from django.conf import settings

from ieia.xblock.load_static import LoadStatic


external_editors = getattr(settings, 'ORA_AVAILABLE_EDITORS', {})

default_editors = {
    'text': {
        'display_name': 'Simple Text Editor',
        'js': [LoadStatic.get_url('ieia-editor-textarea.js')],
    },
    'tinymce': {
        'display_name': 'WYSIWYG Editor',
        'js': [LoadStatic.get_url('ieia-editor-tinymce.js')],
    },
}

AVAILABLE_EDITORS = {}
AVAILABLE_EDITORS.update(external_editors)
AVAILABLE_EDITORS.update(default_editors)
