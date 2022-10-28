{
    'name': "Popbill HomeTax SMS",  # Module title
    'summary': "Popbill HomeTax SMS",  # Module subtitle phrase
    "license": "OPL-1",
    # 'sequence': '1',
    # 'complexity': 'easy',
    'author': "LinkUp Info Tech",
    'description': """
SMS
==============
SMS service send to customer by Linkup.
    """,
    'category': 'Tools',
    'depends': ['base', 'sms', 'iap', 'mail'],

    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',

    ],
}