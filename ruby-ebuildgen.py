#!/usr/bin/env python3
# ruby-ebuildgen
# Generate ebuild prototypes for rubygems
# 2016 Manuel Rueger <mrueg@gentoo.org>
# Licensed under MIT

import requests
from jinja2 import Environment, FileSystemLoader
import os
import sys
import re
import configargparse
from datetime import date


BASE_URI = 'https://rubygems.org/api/v1'
URI_ALL = '%s/versions/%s.json'
URI_LATEST = '%s/versions/%s/latest.json'
URI_SEARCH = '%s/search.json?query=%s'
RUBY_TARGETS = 'ruby20 ruby21 ruby22 ruby23'


def get_json(pkg_name, pkg_version=None):
    '''
    Connnects to rubygems.org API and requests information for the specified
    package. If pkg_version is unset, it will use the latest available version
    :param pkg_name: Name of the package
    :param pkg_version: Version of the package
    :return: Merged and filtered package information from rubygems.org
    '''

    req = requests.get(URI_ALL % (BASE_URI, pkg_name))
    if req.status_code != 200:
        sys.stderr.write("Could not find requested package %s on rubygems.org,"
                         " HTTP Status: %s" % (pkg_name, req.status_code))
        exit(-1)
    pkg_all = req.json()

    if pkg_version is None:
        req = requests.get(URI_LATEST % (BASE_URI, pkg_name))
        if req.status_code != 200:
            sys.stderr.write("Could not find requested package %s on "
                             "rubygems.org, HTTP Status: %s"
                             % (pkg_name, req.status_code))
            exit(-1)
        pkg_latest = req.json()
        pkg_version = pkg_latest['version']

    req = requests.get(URI_SEARCH % (BASE_URI, pkg_name))
    if req.status_code != 200:
        sys.stderr.write("Could not find requested package %s on rubygems.org,"
                         " HTTP Status: %s" % (pkg_name, req.status_code))
        exit(-1)
    pkg_search = req.json()

    for pkg in pkg_search:
        if pkg['name'] == pkg_name:
            res_pkg_search = pkg
            pass

    try:
        res_pkg_search
    except Exception:
        sys.stderr.write("%s not found in API search response" % (pkg_name))
        exit(-1)

    for pkg in pkg_all:
        if pkg['number'] == pkg_version:
            res_pkg = pkg
            pass
    try:
        res_pkg
    except Exception:
        sys.stderr.write("%s not found in API all response" % (pkg_name))
        exit(-1)

    return res_pkg_search, res_pkg


def craft_json(res_pkg, res_pkg_search):
    '''
    Generates a suitable json based on the information
    '''

    ebuildgen = {}

    try:
        ebuildgen['version'] = res_pkg['version']
    except KeyError:
        sys.write.stdout("No version given")
        exit(-1)

    ebuildgen['licenses'] = set()
    try:
        ebuildgen['licenses'].update(res_pkg_search['licenses'])
    except KeyError:
        pass
    try:
        ebuildgen['licenses'].update(res_pkg['licenses'])
    except KeyError:
        pass

    ebuildgen['description'] = ''
    try:
        ebuildgen['description'] = res_pkg_search['description']
    except KeyError:
        pass
    if ebuildgen['description'] == '':
        try:
            ebuildgen['description'] = res_pkg_search['summary']
        except KeyError:
            pass
    try:
        ebuildgen['description'] = res_pkg['description']
    except KeyError:
        pass
    if ebuildgen['description'] == '':
        try:
            ebuildgen['description'] = res_pkg_search['summary']
        except KeyError:
            pass

    ebuildgen['homepage'] = set()
    try:
        ebuildgen['homepage'].add(res_pkg['homepage_uri'])
    except KeyError:
        pass
    try:
        ebuildgen['homepage'].add(res_pkg['project_uri'])
    except KeyError:
        pass
    try:
        ebuildgen['homepage'].add(res_pkg['source_code_uri'])
    except KeyError:
        pass

    ebuildgen['licenses'] = filter(None, ebuildgen['licenses'])

    try:
        ebuildgen['licenses'] = ' '.join(ebuildgen['licenses'])
    except Exception:
        ebuildgen['licenses'] = ''

    ebuildgen['homepage'] = filter(None, ebuildgen['homepage'])

    try:
        ebuildgen['homepage'] = ' '.join(ebuildgen['homepage'])
    except Exception:
        ebuildgen['homepage'] = ''

    rdeps = create_deps(res_pkg['dependencies']['runtime'])
    if rdeps:
        ebuildgen['rdeps'] = 'ruby_add_rdepend \"%s\"' % rdeps
    else:
        ebuildgen['rdeps'] = ''
    bdeps = create_deps(res_pkg['dependencies']['development'])
    if bdeps:
        ebuildgen['bdeps'] = 'ruby_add_bdepend \"%s\"' % bdeps
    else:
        ebuildgen['bdeps'] = ''

    return ebuildgen


def create_deps(dependencies):
    calc_deps = []

    for dep in dependencies:
        for req in str.split(dep['requirements'], ', '):
            depoperator, depversion = str.split(req, ' ')
            separator = '-'
            if depversion == '0':
                depversion = separator = depoperator = ''
            if depoperator == '~>':
                depoperator = ">="
                calc_deps.append('%sdev-ruby/%s%s%s' % (depoperator,
                                                        dep['name'], separator,
                                                        depversion))
                depoperator = "<"
                depversion = re.split(r'\.', depversion)
                depversion = depversion[0:-1]
                depversion[-1] = str(int(depversion[-1]) + 1)
                depversion = '.'.join(depversion)
                calc_deps.append('%sdev-ruby/%s%s%s' % (depoperator,
                                                        dep['name'], separator,
                                                        depversion))
            else:
                calc_deps.append('%sdev-ruby/%s%s%s' % (depoperator,
                                                        dep['name'], separator,
                                                        depversion))

    return '\n\t'.join(calc_deps)


def create_ebuild(package_name, version, targets, stdout):
    '''
    Creates an ebuild based on the response from rubygems.org and a template
    ebuild using jinja2
    :param package_name: Name of the package
    :param version: Version of the package
    :param targets: Ruby targets to be included in USE_RUBY
    '''

    template_dir = os.path.dirname(os.path.abspath(__file__))
    jj2_env = Environment(loader=FileSystemLoader(template_dir),
                          trim_blocks=True)
    res_pkg_search, res_pkg = get_json(package_name, version)
    ebuildgen = craft_json(res_pkg_search, res_pkg)
    ebuildgen['ruby_targets'] = targets
    ebuildgen['year'] = date.today().year

    if stdout is True:
        print(jj2_env.get_template('ruby.ebuild.tpl').render(
            ebuildgen=ebuildgen))
    else:
        filename = "%s-%s.ebuild" % (package_name,  ebuildgen['version'])
        with open(filename, 'w+') as f:
            f.write(jj2_env.get_template('ruby.ebuild.tpl').render(
                ebuildgen=ebuildgen))


def main():
    p = configargparse.ArgumentParser()

    p.add_argument('-p', '--package', required=True, help='Package name')
    p.add_argument('-v', '--version', help='Package version', default=None)
    p.add_argument('-t', '--targets', help='Ruby targets',
                   default=RUBY_TARGETS)
    p.add_argument('-o', help='Write to stdout instead of creating a file',
                   action='store_true')
    options = p.parse_args()

    create_ebuild(options.package, options.version, options.targets, options.o)

if __name__ == '__main__':
    main()
