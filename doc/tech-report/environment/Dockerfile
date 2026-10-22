# Linux amd64, Python 3.11.13, Debian 12; immutable multi-platform image digest.
FROM python:3.11.13-bookworm@sha256:4d88a40c18f95eacef39350c1162fa0b7846a8dd1c55311e1e5a60825b7cd6e6
# The snapshot locks the complete apt dependency closure, including TeX Live 2022.
RUN rm /etc/apt/sources.list.d/debian.sources && \
    printf '%s\n' 'deb [check-valid-until=no] https://snapshot.debian.org/archive/debian/20250929T000000Z bookworm main' \
    'deb [check-valid-until=no] https://snapshot.debian.org/archive/debian-security/20250929T000000Z bookworm-security main' > /etc/apt/sources.list && \
    apt-get update && apt-get install -y --no-install-recommends \
    libnetcdf-dev netcdf-bin autoconf automake libtool pkg-config \
    texlive-luatex texlive-latex-extra texlive-science texlive-fonts-recommended \
    texlive-bibtex-extra fonts-texgyre poppler-utils librsvg2-bin && \
    dpkg-query -W > /opt/system-packages.lock && rm -rf /var/lib/apt/lists/*
RUN git clone https://github.com/universal-ctags/ctags /tmp/ctags && \
    cd /tmp/ctags && git checkout b8eb0da4121372b5d74a90fc36cba6a31f147f3c && \
    ./autogen.sh && ./configure --disable-json --disable-xml --disable-yaml --disable-seccomp && \
    make -j2 && make install && rm -rf /tmp/ctags
COPY python.lock /opt/python.lock
RUN pip install --no-cache-dir --no-deps -r /opt/python.lock && pip check
RUN curl -fLsS https://github.com/quarto-dev/quarto-cli/releases/download/v1.10.19/quarto-1.10.19-linux-amd64.tar.gz -o /tmp/quarto.tar.gz && \
    echo '8e38c2b2df6a6dbd369ea16e15acded6894545258d13a02f777f81ad18fd7973  /tmp/quarto.tar.gz' | sha256sum -c - && \
    tar -xzf /tmp/quarto.tar.gz -C /opt && rm /tmp/quarto.tar.gz
ENV PATH="/opt/quarto-1.10.19/bin:${PATH}" \
    QUARTO_TEXLIVE_BINPATH=/usr/bin \
    QUARTO_PYTHON=/usr/local/bin/python
