export default function Head() {
    return (
        <>
            <script
                dangerouslySetInnerHTML={{
                    __html: `
            (function () {
              try {
                var theme = localStorage.getItem('theme');
                if (theme === 'system' || !theme) {
                  var systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
                  document.documentElement.classList.add(systemTheme);
                  document.documentElement.style.colorScheme = systemTheme;
                } else {
                  document.documentElement.classList.add(theme);
                  document.documentElement.style.colorScheme = theme;
                }
              } catch (_) {}
            })();
          `,
                }}
            />
        </>
    );
}