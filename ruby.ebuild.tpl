# Copyright 1999-{{ ebuildgen.year }} Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Id$

EAPI=5

USE_RUBY="{{ ebuildgen.ruby_targets }}"

inherit ruby-fakegem

DESCRIPTION="{{ ebuildgen.description }}"
HOMEPAGE="{{ ebuildgen.homepage }}"

LICENSE="{{ ebuildgen.licenses }}"
SLOT="0"
KEYWORDS="~amd64"
IUSE=""

{% if ebuildgen.rdeps %}
{{ ebuildgen.rdeps -}}
{% endif %}
{% if ebuildgen.bdeps %}

{{ ebuildgen.bdeps -}}
{% endif %}
