# Security Policy

Is repo ka automation kaise secure rakha gaya hai — ye sab yahan likha hai.

---

## 🔐 Token ke baare me

Ye project **Personal Access Token** use karta hai GitHub API se baat karne ke liye.

**Sirf fine-grained token hi use karein.** Classic token (`ghp_...`) poori account
ka access deta hai — wo zaroorat se zyada hai.

| | Fine-grained ✅ | Classic ❌ |
|---|---|---|
| Kitne repos | sirf jo aap choose karein | aapke **saare** repos |
| Permissions | bilkul specific | poori account |
| Risk agar leak ho | 1 repo tak limited | pura account |

### Token set karne ke sahi tareeke

1. **Fine-grained** token banayein:
   `Settings → Developer settings → Personal access tokens → Fine-grained tokens`

2. **Resource owner:** apna account

3. **Repository access:** `Only select repositories` → sirf ye chunein:
   - `Abhijeet-Kumar-Prajapati/Abhijeet-Kumar-Prajapati` (profile README)
   - `Web-Media-Player` (topics sync)

4. **Repository permissions:**
   - `Contents` → **Read and write**
   - `Metadata` → **Read-only** (ye apne aap on rehta hai)

5. **Account permissions:**
   - `Profile` → **Read and write** (sirf bio ke liye; na chahiye to hata dein)

6. **Expiration:** `90 days` set karein — reminder aa jayega, phir renew kar lena.
   (`No expiration` se token bhool jaate hain aur kabhi clean nahi hota.)

7. Secret me daalte waqt **Actions → New repository secret → `PROFILE_TOKEN`**.

---

## 🛡️ Jo protections is repo me hain

| Protection | Kahan |
|---|---|
| Actions **SHA se pinned** hain | `.github/workflows/auto-update.yml` |
| Sirf `contents: write` permission | workflow ke `permissions:` block me |
| `persist-credentials: false` | checkout step me (token disk par nahi bachta) |
| `timeout-minutes: 10` | koi script hang na ho |
| `concurrency` lock | do runs ek saath na chale |
| Har step alag `try/except` me | ek fail ho to baaki chale |
| **Idempotent** commits | kuch nahi badla to commit hi nahi |
| Topics **merge** hote hain, delete nahi | koi existing topic kho nahi jata |
| README ke sirf `AUTO` blocks badalte hain | aapka content safe rehta hai |
| `.env` gitignore me hai | token kabhi commit nahi hoga |

---

## 🚨 Agar token leak ho jaye

Turant ye karo:

1. `Settings → Developer settings → Personal access tokens`
2. Us token ke samne **Revoke / Delete** dabao
3. Naya token bana kar secret me update karo
4. `Actions` tab me purane runs ka log dekh lo

> Yaad rakhein: **kisi ko token mat bhejein**, screenshot me bhi na dikhe.

---

## ✅ Aur bhi accha karna ho to

- **2FA** on karein — `Settings → Password and authentication`
- **Dependabot** on karein — `Settings → Code security → Dependabot alerts`
- **Secret scanning** on karein — `Settings → Code security → Secret scanning`

Yeh teeno GitHub Free me available hain aur aapke account ko protect karte hain.