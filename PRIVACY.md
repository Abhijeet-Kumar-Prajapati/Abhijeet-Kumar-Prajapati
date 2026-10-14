# Privacy & Identity Guide

Ye document batata hai ki aapki profile **kahan tak secure** ho sakti hai —
aur kahan par **koi bhi promise nahi** kar sakta.

---

## 🔴 Issue #1: Aapki email PUBLIC hai (abhi bhi)

Audit me pata chala ki aapke dono repos ki commit history me aapka
**asli email** pada hai:

```
abhijeet943935@gmail.com  →  ABHIJEET KUMAR PRAJAPATI
```

Ye spam bots me already collect ho sakta hai. Bot chahiye to 1 minute me
aapko spam/harassment mail aa sakta hai.

### Fix karein

**1. Naye commits ka email chhupaen — Settings → Emails**
```
https://github.com/settings/emails
```
- ✅ **"Keep my email addresses private"** ON kar dein
- Neeche ek **noreply email** dikhega, jaise:
  `12345678+Abhijeet-Kumar-Prajapati@users.noreply.github.com`
  use **copy** kar lein

**2. Git me default email set karein** (PC me ek baar)

Git install karne ke baad:
```bash
git config --global user.email "12345678+Abhijeet-Kumar-Prajapati@users.noreply.github.com"
git config --global user.name "Abhijeet Kumar Prajapati"
```
Ab har naye commit par email **chhupi** hui email jayegi.

**3. Purane commits?**

Wo 4 purane commits abhi bhi email dikha rahe hain. Options:

| Option | Kaisa hai |
|---|---|
| **Chhod dein** | Sabse aasaan. Risk sirf spam hai — account hack nahi hoga. |
| **Repo dobara banao** | Repo me sirf 2-3 commits hain, to naya repo bana kar sirf `index.html` upload karein — purana delete. Email gayab ho jayegi. |

> ⚠️ **Sachai:** purane commit ka email ek baar public ho gaya to use
> "undelete" nahi kar sakte. Lekin usse account tak **koi access nahi**
> milta — sirf spam risk hai.

---

## 📸 Photo par sachai (ye padhna zaroori hai)

Aapne kaha "koi meri photo kharab na kar sake." Main aapko **jhooth nahi
bolunga** — ye clearly bata deta hूँ:

### ❌ Jo main VAADDE nahi kar sakta

- Koi bhi aapki profile/photo **screenshot** nahi le sakta, ye rok nahi sakte
- Jo kuch **public** ho gaya, wo un-download nahi hota
- Koi aapko **stalk** nahi kar sakta, ye control nahi hai

### ✅ Jo main ACTUALLY kar sakta hoon

| Protection | Kaise |
|---|---|
| **Photo hi na ho** | Avatar ko **illustration / logo / initials** se replace karein. Isse face publicly nahi hai. |
| **Repo me personal photo na ho** | Kisi bhi repo me apni photo mat rakhein |
| **Personal data na ho** | README me phone number, address, DOB, Aadhaar — **kabhi nahi** |
| **Email chhupi** | Noreply email use karein (upar dekha) |
| **Location coarse rakhein** | `"India"` likhein, `"Full address"` nahi |
| **Personal account alag** | Personal cheezein alag account/browsing profile me |

### 🛡️ Sabse strong option

Agar **bilkul** nahi chahte ki aapki photo kahi public dikhe:

> Avatar hata dein ya **illustration** laga dein.
> `Settings → Profile picture → Remove`

Phir koi photo nahi hai — na download, na misuse, na stalk.

**Trade-off:** recruiters ke liye professional dikhna kam hoga.
Aapka call hai — lekin jaan-boojh kar karein, na ki majboor me.

---

## 📞 Phone number public karein — sachai

Aapne kaha ki recruiters ko phone dikhe. Maine daal diya hai — par ye jaan
boojh kar karna zaroori hai.

### ❌ Kya risk hai

- Number **scrapers** se collect hota hai (public web pe numbers 10 din me mil
  jaate hain)
- Is number par **spam calls / SMS fraud** aa sakte hain — khaas kar
  "bank OTP" wale fraud
- Koi number se **SIM swap / social engineering** try kar sakta hai
- Blocklist databases me number daal diya ja sakta hai

### ✅ Kya accha hoga

- Recruiters seedha call/WhatsApp kar sakte hain
- BTech students ke liye ye **bilkul normal** practice hai — recruiters
  ise expect karte hain

### 🛡️ Balance banayein

Ye sab aap pehle se kar rahe hain:

| Protection | Kaise |
|---|---|
| **"Email first"** | Phone section me likha hai ki pehle email karein — isi se 90% spam calls ruk jayenge |
| **Time limit** | Sirf 10 AM IST ke baad — raat ko call nahi |
| **Kabhi badalna ho** | `config.json` me `show_phone: false` — bas. Auto update ho jayega |
| **WhatsApp number alag** | Agar WhatsApp number alag hai, wo `phone_display` me daalein |

### Ek aur baat

Phone **badge image (shields.io)** me nahi daala gaya. Agar badge hota,
to number ek **third-party server** (shields.io) par jaata aur cache hota.
Plain text me ye nahi hota — isliye plain text rakha gaya hai.

### 💡 Mera suggestion

```
config.json me aise rakhein:
"show_email": true,     <- zaroor chahiye
"show_phone": true,     <- jab tak aap comfortable ho
```

Job milne ke baad resume/LinkedIn par number de sakte hain. Tab tak
**email hi primary** rakhein — recruiters usi par reply karte hain.

---

## 🛡️ Hack / account security

Ye cheezein **100% aapke control** me hain:

| Kya | Kahan | Status |
|---|---|---|
| **2FA** on | Settings → Password and authentication | ❌ abhi nahi |
| **Fine-grained token** | Developer settings → PAT | ✅ setup kar rahe hain |
| **Secret scanning** | Settings → Code security | ❌ abhi nahi |
| **Dependabot alerts** | Settings → Code security | ❌ abhi nahi |
| **Email privacy** | Settings → Emails | ❌ abhi nahi |

### 2FA sabse zaroori hai

Aapke account me sirf **1 follower** hai, koi token leak hone par risk
kam hai — lekin 2FA ke bina koi password guess karke account le sakta hai.

**2FA on karein — 2 minute lagte hain aur 99% attacks ruk jate hain.**
(Authenticator app use karein, SMS se behtar hai.)

---

## ✅ Summary — kya kya ho chuka hai

| Item | Status |
|---|---|
| Token fine-grained + minimal permission | ✅ |
| Token sirf selected repos tak | ✅ |
| Actions SHA-pinned | ✅ |
| Workflow minimal permissions | ✅ |
| Token gitignore + `.env` | ✅ |
| Topics merge (delete nahi) | ✅ |
| README user content protected | ✅ |
| Idempotent (no commit if no change) | ✅ |
| Email chhupi (noreply) | ⬜ karenge |
| 2FA | ⬜ karenge |
| Dependabot + secret scanning | ⬜ karenge |
| Avatar (photo vs illustration) | ⬜ aapki choice |

---

> **Bottom line:** Software aur configuration ko 100% secure kar sakte hain.
> **Social/identity privacy ka koi 100% protection nahi hota** — jo public
> hai wo public rahega. Isliye hum wo cheezein **public hi na karein**
> j ki zarurat nahi — jo upar bataya gaya hai, wahi karein.