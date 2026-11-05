# How should passwords be stored against offline guessing? / 如何存储密码以抵抗离线猜测？

Store a salted password hash from a password-storage algorithm designed to make guessing expensive, such as Argon2id. A unique random salt is stored with each hash; it is not a secret. A fast digest such as SHA-256 alone is not a password-storage scheme. Use a maintained library and tune its cost for the deployment, then combine it with online attempt throttling. / 使用专为提高猜测成本而设计的密码存储算法保存带盐哈希，例如 Argon2id。每个哈希保存一个唯一随机 salt；salt 不是秘密。单独使用 SHA-256 这类快速摘要并非密码存储方案。使用维护良好的库并根据部署调节成本，再配合在线尝试限速。

**Key terms / 关键术语：** password hash / 密码哈希；salt / 盐；Argon2id / Argon2id 算法；pepper / 秘密 pepper；offline guessing / 离线猜测；rate limiting / 速率限制。

A pepper may add defense in depth when stored separately from the password database, but it is not a replacement for a suitable password hash. Keep the pepper in a secret store with its own rotation and access policy. Use password policy and attempt throttling to reduce online guessing as well.

**Related notes / 相关笔记：** [Web Security and Authentication / Web安全与身份认证](web-security-and-authentication.md) covers the login/session context; [How do web services limit denial-of-service impact? / Web 服务如何限制拒绝服务的影响？](web-availability-and-ddos.md) covers request rate and resource limits.

**Sources / 来源：** OWASP [Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html) and [NIST SP 800-63B-4](https://pages.nist.gov/800-63-4/sp800-63b.html), checked 2026-10-15.
