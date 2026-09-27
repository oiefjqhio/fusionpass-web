#!/usr/bin/env python3
"""Apply the Fusion Pass branding and lock-down to a stremio-web checkout.
Idempotent: run after every upstream sync (git merge upstream/development, then this, commit).

GPL-2.0: this fork's source stays public. Sign-in is the Fusion Pass email and password
(each pass is a Stremio account); the look follows the Fusion Pass (Nuvio-based) apps.
"""
import glob, os, shutil, struct, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = f'{ROOT}/src'
OUT = f'{ROOT}/fusionpass/brand/out'
SITE = 'https://fusionpass.shop'
changed = []


def edit(path, pairs):
    s = open(path, encoding='utf8').read()
    orig = s
    for a, b in pairs:
        if a not in s and b not in s:
            sys.exit(f'rebrand: anchor not found in {path}: {a[:80]!r} (upstream changed; update rebrand.py)')
        s = s.replace(a, b)
    if s != orig:
        open(path, 'w', encoding='utf8').write(s)
        changed.append(os.path.relpath(path, ROOT))


def copy(src, dst):
    if not os.path.exists(dst) or open(dst, 'rb').read() != open(src, 'rb').read():
        shutil.copyfile(src, dst)
        changed.append(os.path.relpath(dst, ROOT))


# 1. Images: icons, logo, iPhone splash screens, favicon (a PNG inside an .ico).
for f in glob.glob(f'{OUT}/*.png') + glob.glob(f'{OUT}/splash/*.jpg'):
    rel = os.path.relpath(f, OUT)
    if rel == 'favicon-256.png':
        continue
    copy(f, f'{ROOT}/assets/images/{rel}')
png = open(f'{OUT}/favicon-256.png', 'rb').read()
ico = struct.pack('<HHH', 0, 1, 1) + struct.pack('<BBBBHHII', 0, 0, 0, 0, 1, 32, len(png), 22) + png
for name in ['favicon.ico']:
    dst = f'{ROOT}/assets/favicons/{name}'
    if not os.path.exists(dst) or open(dst, 'rb').read() != ico:
        open(dst, 'wb').write(ico)
        changed.append(os.path.relpath(dst, ROOT))

# 2. Name and colours in the page shell and the install manifest.
edit(f'{SRC}/index.html', [
    ('<meta name="apple-mobile-web-app-title" content="Stremio">', '<meta name="apple-mobile-web-app-title" content="Fusion Pass">'),
    ('<meta name="theme-color" content="#2a2843">', '<meta name="theme-color" content="#0D0D0D">'),
    ('<title>Stremio - Freedom to Stream</title>', '<title>Fusion Pass</title>'),
])
edit(f'{ROOT}/manifest.json', [
    ('"name": "Stremio Web"', '"name": "Fusion Pass"'),
    ('"short_name": "Stremio"', '"short_name": "Fusion Pass"'),
    ('"description": "Freedom To Stream"', '"description": "Watch with your Fusion Pass"'),
    ('"background_color": "#0c0b11"', '"background_color": "#0D0D0D"'),
    ('"theme_color": "#2a2843"', '"theme_color": "#0D0D0D"'),
    ('"label": "Homescreen of Stremio"', '"label": "Fusion Pass"'),
])

# 3. The Fusion Pass app palette (Nuvio base: near-black, neutral greys) with our violet accent.
edit(f'{SRC}/App/styles.less', [
    ('--primary-background-color: rgba(12, 11, 17, 1);', '--primary-background-color: rgba(13, 13, 13, 1);'),
    ('--secondary-background-color: rgba(26, 23, 62, 1);', '--secondary-background-color: rgba(36, 36, 36, 1);'),
    ('--primary-foreground-color: rgba(255, 255, 255, 0.9);', '--primary-foreground-color: rgba(245, 247, 248, 1);'),
    ('--secondary-foreground-color: rgb(12, 11, 17, 1);', '--secondary-foreground-color: rgb(13, 13, 13, 1);'),
    ('--primary-accent-color: rgb(123, 91, 245);', '--primary-accent-color: rgb(123, 108, 255);'),
    ('--modal-background-color: rgba(15, 13, 32, 1);', '--modal-background-color: rgba(26, 26, 26, 1);'),
    ('--outer-glow: 0px 0px 15px rgba(123, 91, 245, 0.37);', '--outer-glow: 0px 0px 15px rgba(123, 108, 255, 0.37);'),
])
edit(f'{SRC}/routes/Intro/styles.less', [
    ("background: url('/assets/images/background_1.svg'), url('/assets/images/background_2.svg');",
     "background: radial-gradient(120% 80% at 50% 0%, rgba(123, 108, 255, 0.22), rgba(13, 13, 13, 0) 60%), var(--primary-background-color);"),
])

# 4. Every visible "Stremio" in the interface text becomes Fusion Pass.
edit(f'{SRC}/index.js', [
    ("""const translations = Object.fromEntries(Object.entries(stremioTranslations()).map(([key, value]) => [key, {
    translation: value
}]));""", """// Fusion Pass: our name in every language.
const rename = (v) => typeof v === 'string' ? v.replace(/Stremio/g, 'Fusion Pass') : v;
const translations = Object.fromEntries(Object.entries(stremioTranslations()).map(([key, value]) => [key, {
    translation: Object.fromEntries(Object.entries(value).map(([k, v]) => [k, rename(v)]))
}]));"""),
])

# 5. Sign-in: Fusion Pass email + password only. No sign-up, guest, Facebook or Apple (accounts
#    come with the pass) and no password reset (it would split the pass login from this one).
I = f'{SRC}/routes/Intro/Intro.js'
edit(I, [
    ("""                            <div className={styles['forgot-password-link-container']}>
                                <Button className={styles['forgot-password-link']} onClick={openPasswordRestModal}>{t('FORGOT_PASSWORD')}</Button>
                            </div>""", """                            null /* Fusion Pass: no password reset here */"""),
])
s = open(I, encoding='utf8').read()
start = s.find("                <div className={styles['options-container']}>")
end = s.find("            {\n                passwordRestModalOpen ?", start)
if start != -1 and end != -1:
    s = s[:start] + "                {/* Fusion Pass: sign-in with the pass email and password only */}\n            </div>\n" + s[end:]
    open(I, 'w', encoding='utf8').write(s)
    changed.append(os.path.relpath(I, ROOT))
elif 'Fusion Pass: sign-in with the pass email' not in s:
    sys.exit('rebrand: Intro options block not found')

edit(I, [
    ("form: [LOGIN_FORM, SIGNUP_FORM].includes(queryParams.get('form')) ? queryParams.get('form') : SIGNUP_FORM,",
     "form: LOGIN_FORM, // Fusion Pass: log-in only"),
    ("        if ([LOGIN_FORM, SIGNUP_FORM].includes(queryParams.get('form'))) {",
     "        if ([LOGIN_FORM].includes(queryParams.get('form'))) { // Fusion Pass: log-in only"),
])

# 6. No addon catalogue (the account comes set up; never torrents) and no magnet links.
edit(f'{SRC}/components/MainNavBars/MainNavBars.tsx', [
    ("    { id: 'addons', label: 'ADDONS', icon: 'addons', href: '/addons' },\n", ''),
])
N = f'{SRC}/components/NavBar/HorizontalNavBar/NavMenu/NavMenuContent.js'
edit(N, [
    ("""                <Button className={styles['nav-menu-option-container']} title={ t('ADDONS') } href={'#/addons'}>
                    <Icon className={styles['icon']} name={'addons-outline'} />
                    <div className={styles['nav-menu-option-label']}>{ t('ADDONS') }</div>
                </Button>
                <Button className={styles['nav-menu-option-container']} title={ t('PLAY_URL_MAGNET_LINK') } onClick={onPlayMagnetLinkClick}>
                    <Icon className={styles['icon']} name={'magnet-link'} />
                    <div className={styles['nav-menu-option-label']}>{ t('PLAY_URL_MAGNET_LINK') }</div>
                </Button>
""", ''),
    ("href={'https://stremio.zendesk.com/'}", f"href={{'{SITE}/setup'}}"),
    ("href={'https://www.stremio.com/tos'}", f"href={{'{SITE}/terms'}}"),
    ("href={'https://www.stremio.com/privacy'}", f"href={{'{SITE}/privacy'}}"),
    ("href={'https://www.stremio.com/acc-settings'}", f"href={{'{SITE}/account'}}"),
])
edit(f'{SRC}/routes/MetaDetails/StreamsList/StreamsList.js', [
    ("""        return !profile || profile.auth === null || profile.auth?.user?.isNewUser === true && !video?.upcoming;""",
     """        return false; // Fusion Pass: no addon catalogue"""),
])

# 7. Our site is a trusted link target (no "leaving the app" prompt).
edit(f'{SRC}/common/CONSTANTS.js', [
    ("const WHITELISTED_HOSTS = ['stremio.com',", "const WHITELISTED_HOSTS = ['fusionpass.shop', 'stremio.com',"),
])

# 8. Our own log-in copy, and no "install the streaming server" nags (playback goes to the
#    browser or an external player; the Stremio server is never part of Fusion Pass).
edit(f'{SRC}/routes/Intro/Intro.js', [
    ("{t('WEBSITE_SLOGAN_NEW_NEW')}", "{'Welcome back'}"),
    ("{t('WEBSITE_SLOGAN_ALL')}", "{'Use the email and password from your pass.'}"),
])
edit(f'{SRC}/routes/Board/Board.js', [
    ("        return streamingServer.settings !== null && streamingServer.settings.type === 'Err' && (",
     "        return false && streamingServer.settings !== null && streamingServer.settings.type === 'Err' && ( // Fusion Pass"),
])
edit(f'{SRC}/components/NavBar/HorizontalNavBar/NavMenu/NavMenuContent.js', [
    ("        return streamingServer.settings !== null && streamingServer.settings.type === 'Ready' || (",
     "        return true || streamingServer.settings !== null && streamingServer.settings.type === 'Ready' || ( // Fusion Pass"),
])

# 9. Settings: our support/legal/source links; no Trakt (owner decision, same as the apps), and no
#    password change or account deletion here (they would split the pass login; done on our site).
G = f'{SRC}/routes/Settings/General/General.tsx'
edit(G, [
    ("href={'https://stremio.zendesk.com/hc/en-us'}", f"href={{'{SITE}/setup'}}"),
    ("href={`https://github.com/stremio/stremio-web/tree/${process.env.COMMIT_HASH}`}",
     "href={`https://github.com/oiefjqhio/fusionpass-web/tree/${process.env.COMMIT_HASH}`}"),
    ("""                href={'https://www.stremio.com/tos'}
            />""", f"""                href={{'{SITE}/terms'}}
            />"""),
    ("""                href={'https://www.stremio.com/privacy'}
            />""", f"""                href={{'{SITE}/privacy'}}
            />"""),
    ("""            {
                profile?.auth?.user &&
                    <Link
                        label={t('SETTINGS_ACC_DELETE')}
                        href={'https://stremio.zendesk.com/hc/en-us/articles/360021428911-How-to-delete-my-account'}
                    />
            }
            {
                profile?.auth?.user?.email &&
                    <Link
                        label={t('SETTINGS_CHANGE_PASSWORD')}
                        href={`https://www.strem.io/reset-password/${profile.auth.user.email}`}
                    />
            }
            <Option className={styles['trakt-container']} icon={'trakt'} label={t('SETTINGS_TRAKT')}>
                <Button className={'button'} title={isTraktAuthenticated ? t('LOG_OUT') : t('SETTINGS_TRAKT_AUTHENTICATE')} disabled={profile.auth === null} tabIndex={-1} onClick={onToggleTrakt}>
                    {isTraktAuthenticated ? t('LOG_OUT') : t('SETTINGS_TRAKT_AUTHENTICATE')}
                </Button>
            </Option>
""", """            {/* Fusion Pass: no account deletion, password change or Trakt here */}
"""),
])

print('rebrand: ok,', len(changed), 'changes')
for c in changed[:80]:
    print('  ', c)
