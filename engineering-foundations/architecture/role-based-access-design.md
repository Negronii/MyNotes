# How should roles control access to a feature? / 角色怎样控制对功能的访问？

Map roles to permissions and evaluate them for the actual request and resource. A menu can reflect what the user may do, while the service enforces the same policy for each action. / 把角色映射为权限，并针对实际请求与资源评估。界面菜单可以反映用户可执行的操作，服务仍需在每次操作时实施策略。

## How does Role-Based Access Control (RBAC) work?

**基于角色的访问控制 / Role-Based Access Control** associates permissions with roles and assigns users to roles. It is one authorization model; it does not determine whether a particular user may access every object of a type.

A relational model commonly includes:

- **User / 用户**: identity and credential reference.
- **Role / 角色**: named job or application role.
- **Permission / 权限**: action on a resource or capability.
- **UserRole / 用户角色**: many-to-many user-to-role assignment.
- **RolePermission / 角色权限**: many-to-many role-to-permission assignment.

A request is authenticated first, then the server checks whether the resulting subject may perform the requested action on the requested object. Check every protected operation and resource; hiding a button or trusting a client-supplied role is not authorization. Role changes simplify policy administration only when the application's permission model fits roles.

See [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html) for authorization boundaries and [Design Patterns: Elements of Reusable Object-Oriented Software](https://www.informit.com/store/design-patterns-elements-of-reusable-object-oriented-software-9780201633610) for the original GoF catalog.

[Back to the main question / 返回主问题](design-patterns-in-practice.md).
