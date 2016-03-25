# Copyright 1999-{{ ebuildgen.year }} Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Id$

EAPI=5

RUBY_TARGETS="{{ ebuildgen.ruby_targets }}"

inherit ruby-fakegem

DESCRIPTION="{{ ebuildgen.description }}"
HOMEPAGE="{{ ebuildgen.homepage }}"

LICENSE="{{ ebuildgen.licenses }}"
SLOT="0"
KEYWORDS="~amd64"
IUSE=""

{{ ebuildgen.rdeps -}}
{{ ebuildgen.bdeps -}}
