# Copyright (c) 2008 Joost Cassee
# Licensed under the terms of the MIT License (see LICENSE.txt)

import json
import logging

from django.http import HttpResponse
from django.shortcuts import render as render_to_response
from django.shortcuts import render
from django.utils.datastructures import MultiValueDictKeyError
try:
    from django.utils.encoding import force_str as force_text
except ImportError:
    from django.utils.encoding import force_text # Django 3 fallback
from django.template import RequestContext
try:
    from django.utils.translation import gettext as _
except ImportError:
    from django.utils.translation import ugettext as _ # Django 3 fallback

from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse

from tinymce.compressor import gzip_compressor

try:
    import enchant
except ImportError:
    enchant = None


@csrf_exempt
def spell_check(request):
    """
    Returns a HttpResponse that implements the TinyMCE spellchecker protocol.
    """
    try:
        if not enchant:
            raise RuntimeError("install pyenchant for spellchecker functionality")

        raw = force_text(request.body)
        input = json.loads(raw)
        id = input['id']
        method = input['method']
        params = input['params']
        lang = params[0]
        arg = params[1]

        if not enchant.dict_exists(str(lang)):
            raise RuntimeError("dictionary not found for language {!r}".format(lang))

        checker = enchant.Dict(str(lang))

        if method == 'checkWords':
            result = [word for word in arg if word and not checker.check(word)]
        elif method == 'getSuggestions':
            result = checker.suggest(arg)
        else:
            raise RuntimeError("Unknown spellcheck method: {!r}".format(method))
        output = {
            'id': id,
            'result': result,
            'error': None,
        }
    except Exception:
        logging.exception("Error running spellchecker")
        return HttpResponse(_("Error running spellchecker"))
    return HttpResponse(json.dumps(output),
                        content_type='application/json')


def flatpages_link_list(request):
    """
    Returns a HttpResponse whose content is a Javascript file representing a
    list of links to flatpages.
    """
    from django.contrib.flatpages.models import FlatPage
    link_list = [(page.title, page.url) for page in FlatPage.objects.all()]
    return render_to_link_list(link_list)


def compressor(request):
    """
    Returns a GZip-compressed response.
    """
    return gzip_compressor(request)


def render_to_link_list(link_list):
    """
    Returns a HttpResponse whose content is a Javascript file representing a
    list of links suitable for use wit the TinyMCE external_link_list_url
    configuration option. The link_list parameter must be a list of 2-tuples.
    """
    return render_to_js_vardef('tinyMCELinkList', link_list)


def render_to_image_list(image_list):
    """
    Returns a HttpResponse whose content is a Javascript file representing a
    list of images suitable for use wit the TinyMCE external_image_list_url
    configuration option. The image_list parameter must be a list of 2-tuples.
    """
    return render_to_js_vardef('tinyMCEImageList', image_list)


def render_to_js_vardef(var_name, var_value):
    output = "var {!s} = {!s};".format(var_name, json.dumps(var_value))
    return HttpResponse(output, content_type='application/x-javascript')


def filebrowser(request):
    try:
        fb_url = reverse('fb_browse')
    except:
        fb_url = reverse('filebrowser:fb_browse')

    return render(
        request,
        'tinymce/filebrowser.js',
        {'fb_url': fb_url},
        content_type='application/javascript'
    )


def filebrowserPath(request):
    try:
        _dir = request.GET['url']
    except MultiValueDictKeyError:
        _dir = ''

    return render_to_response(
        request,
        'tinymce/defaultpath.js',
        {'dir': _dir,},
        content_type='application/javascript'
    )
