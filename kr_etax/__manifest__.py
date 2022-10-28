{
    "name": "Etax",
    "summary": "Etax",
    "author": "LinkUp Info Tech",
    "license": "AGPL-3",
    "application": True,
    "depends": ["base", "product", "account"],
    "external_dependencies": {"python": ["popbill"]},
    'assets': {
        'web.assets_backend': [
            'kr_etax/static/src/scss/mainwidth.scss',
            'kr_etax/static/src/js/list_renderer.js',
            'kr_etax/static/src/js/form_view.js',
        ],
    },
    "data": [
        "security/hometax_security.xml",
        "security/ir.model.access.csv",
        "data/ir_sequence_data.xml",
        "data/lognote.xml",
        "data/muti_company.xml",
        "views/batch_issue_etax.xml",
        "views/batch_issue_etax_send.xml",
        "views/hometax.xml",
        "views/hometax_move.xml",

    ],

    "qweb": [],
}
