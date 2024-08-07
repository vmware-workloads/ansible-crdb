# ansible-crdb

## Description
This is an Ansible Automation Platform playbook to deploy Cockroach DB v23.2.2 using VM deployed by VMWare Aria Automation. It was designed to work in conjunction with our sample Aria Assembler Blueprint.

This playbook was created for demonstration purposes and should serve as a basis to create a more comprehensive playbook. 


## Playbook Structure

```
ansible-crdb
├── collections
│   └── requirements.yml
├── roles
│   ├── ansible_role_chrony
│   │   └── ...
│   ├── ansible_role_crdb
│   │   └── ...
│   ├── ansible_role_create_user
│   │   └── ...
│   └── ansible_role_kernel_update
│       └── ...
├── deploy.yml
├── LICENSE
└── README.md
```

- `collections/`: directory containing the module requirements for the playbook.
- `roles/`: directory containing the roles.
- `deploy.yml`: the playbook file.
- `LICENSE`: project license.
- `README.md`: instructions and links related to this playbook.

