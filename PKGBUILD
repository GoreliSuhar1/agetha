pkgname=agetha
pkgver=1.0
pkgrel=5
pkgdesc="Agetha AI Desktop Companion"
arch=('any')
license=('MIT')
depends=('python' 'python-pygame' 'python-pillow' 'python-pytesseract' 'python-openai' 'tesseract-data-eng' 'tesseract-data-rus')
install=agetha.install

source=()
sha256sums=()

package() {
    install -d "$pkgdir/opt/agetha"
    cp -r "$startdir"/ai_engine.py \
          "$startdir"/main.py \
          "$startdir"/config.py \
          "$startdir"/screen_reader.py \
          "$startdir"/check_models.py \
          "$startdir"/assets \
          "$startdir"/barrio.ttf \
          "$pkgdir/opt/agetha/"

    # Создаем директорию для бинарников
    install -d "$pkgdir/usr/bin"
    # Создаем скрипт-запускатор
    echo -e '#!/bin/sh\npython3 /opt/agetha/main.py "$@"' > "$pkgdir/usr/bin/agetha"
    # Делаем его исполняемым
    chmod +x "$pkgdir/usr/bin/agetha"
}
