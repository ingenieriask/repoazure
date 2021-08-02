# -*- coding: utf-8 -*-
import logging
import re
from collections import OrderedDict
from threading import local

from rest_framework.views import APIView
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.exceptions import ParseError
from rest_framework.renderers import TemplateHTMLRenderer

from cubes import __version__, browser, cut_from_dict
from cubes.workspace import Workspace, SLICER_INFO_KEYS
from cubes.errors import NoSuchCubeError, ConfigurationError
from cubes.calendar import CalendarMemberConverter
from cubes.browser import Cell, cuts_from_string

from django.conf import settings
from django.http import Http404
from django.core.exceptions import ImproperlyConfigured
from cubes.compat import ConfigParser

API_VERSION = 2

__all__ = [
    'Index', 'ApiVersion', 'Info',
    'ListCubes', 'CubeModel', 'CubeAggregation',
    'CubeCell', 'CubeReport', 'CubeFacts',
    'CubeFact', 'CubeMembers',
]


data = local()


def create_local_workspace(config, cubes_root):
    """
    Returns or creates a thread-local instance of Workspace
    """

    print('data:', data)
    if not hasattr(data, 'workspace'):
        print('workspace:', 'init')
        data.workspace = Workspace(config=config, cubes_root=cubes_root)

    return data.workspace


class ApiVersion(APIView):
    """
    TODO Authentification
    """
    #permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        info = {
            "version": __version__,
            "server_version": __version__,
            "api_version": API_VERSION
        }
        return Response(info)


class CubesView(APIView):
    """
    TODO Authentification
    """
    #permission_classes = (permissions.IsAuthenticated,)
    workspace = None
    SET_CUT_SEPARATOR_CHAR = ';'

    def __init__(self, *args, **kwargs):
        super(CubesView, self).__init__(*args, **kwargs)
        self._fix_cut_separators()

    def _fix_cut_separators(self):
        browser.PATH_ELEMENT = r"(?:\\.|[^:%s|-])*" % self.SET_CUT_SEPARATOR_CHAR
        browser.RE_ELEMENT = re.compile(r"^%s$" % browser.PATH_ELEMENT)
        browser.RE_POINT = re.compile(r"^%s$" % browser.PATH_ELEMENT)
        browser.SET_CUT_SEPARATOR_CHAR = self.SET_CUT_SEPARATOR_CHAR
        browser.SET_CUT_SEPARATOR = re.compile(r'(?<!\\)%s' % self.SET_CUT_SEPARATOR_CHAR)
        browser.RE_SET = re.compile(r"^(%s)(%s(%s))*$" % (
            browser.PATH_ELEMENT, self.SET_CUT_SEPARATOR_CHAR, browser.PATH_ELEMENT
        ))

    def initialize_slicer(self):
        if CubesView.workspace is None:
            try:
                configg = ConfigParser()
                #config = settings.SLICER_CONFIG_FILE
                configg.read(settings.SLICER_CONFIG_FILE)
                cubes_root = settings.SLICER_MODELS_DIR
            except AttributeError:
                raise ImproperlyConfigured('settings.SLICER_CONFIG_FILE and settings.SLICER_MODELS_DIR are not set.')

            print('config:', configg)
            CubesView.workspace = create_local_workspace(config=configg, cubes_root=cubes_root)
            if hasattr(settings, 'SLICER_DEFAULT_DATABASE'):
                #try:
                print('SLICER_DEFAULT_DATABASE:', settings.SLICER_DEFAULT_DATABASE)
                CubesView.workspace.register_store("default", "sql", url=settings.SLICER_DEFAULT_DATABASE)
                print('SLICER_DEFAULT_DATABASE: DONE')
                #except ConfigurationError:
                #  pass

    def get_cube(self, request, cube_name):
        self.initialize_slicer()
        try:
            cube = CubesView.workspace.cube(cube_name, request.user)
        except NoSuchCubeError:
            raise Http404

        return cube

    def get_browser(self, cube):
        return CubesView.workspace.browser(cube)

    def get_cell(self, request, cube, argname="cut", restrict=False):
        """Returns a `Cell` object from argument with name `argname`"""
        converters = {
            "time": CalendarMemberConverter(CubesView.workspace.calendar)
        }

        cuts = []
        for cut_string in request.query_params.getlist(argname):
            cuts += cuts_from_string(
                cube, cut_string, role_member_converters=converters
            )

        if cuts:
            cell = Cell(cube, cuts)
        else:
            cell = None

        if restrict:
            if CubesView.workspace.authorizer:
                cell = CubesView.workspace.authorizer.restricted_cell(
                    request.user, cube=cube, cell=cell
                )
        return cell

    def get_info(self):
        self.initialize_slicer()
        if CubesView.workspace.info:
            info = OrderedDict(CubesView.workspace.info)
        else:
            info = OrderedDict()

        info["cubes_version"] = __version__
        info["timezone"] = CubesView.workspace.calendar.timezone_name
        info["first_weekday"] = CubesView.workspace.calendar.first_weekday
        info["api_version"] = API_VERSION
        return info

    def assert_enabled_action(self, request, browser, action):
        features = browser.features()
        if action not in features['actions']:
            message = u"The action '{}' is not enabled".format(action)
            logging.error(message)
            raise ParseError(detail=message)

    def _handle_pagination_and_order(self, request):
        try:
            page = request.query_params.get('page', None)
        except ValueError:
            page = None
        request.page = page

        try:
            page_size = request.query_params.get('pagesize', None)
        except ValueError:
            page_size = None
        request.page_size = page_size

        # Collect orderings:
        # order is specified as order=<field>[:<direction>]
        order = []
        for orders in request.query_params.getlist('order'):
            for item in orders.split(","):
                split = item.split(":")
                if len(split) == 1:
                    order.append((item, None))
                else:
                    order.append((split[0], split[1]))
        request.order = order

    def initialize_request(self, request, *args, **kwargs):
        original_user = request.user
        request = super(CubesView, self).initialize_request(request, *args, **kwargs)
        self._handle_pagination_and_order(request)
        request.user = original_user
        return request


class Index(CubesView):
    renderer_classes = (TemplateHTMLRenderer,)

    def get(self, request):
        info = self.get_info()
        info['has_about'] = any(key in info for key in SLICER_INFO_KEYS)
        return Response(info, template_name="cubes/index.html")


class Info(CubesView):

    def get(self, request):
        return Response(self.get_info())


class ListCubes(CubesView):

    def get(self, request):
        self.initialize_slicer()
        cube_list = CubesView.workspace.list_cubes(request.user)
        return Response(cube_list)


class CubeModel(CubesView):

    def get(self, request, cube_name):
        cube = self.get_cube(request, cube_name)
        if CubesView.workspace.authorizer:
            hier_limits = CubesView.workspace.authorizer.hierarchy_limits(
                request.user, cube_name
            )
        else:
            hier_limits = None

        model = cube.to_dict(
            expand_dimensions=True,
            with_mappings=False,
            full_attribute_names=True,
            create_label=True,
            hierarchy_limits=hier_limits
        )

        model["features"] = CubesView.workspace.cube_features(cube)
        return Response(model)


class CubeAggregation(CubesView):

    def get(self, request, cube_name):
        cube = self.get_cube(request, cube_name)
        browser = self.get_browser(cube)
        self.assert_enabled_action(request, browser, 'aggregate')

        cell = self.get_cell(request, cube, restrict=True)

        # Aggregates
        aggregates = []
        for agg in request.query_params.getlist('aggregates') or []:
            aggregates += agg.split('|')

        drilldown = []
        ddlist = request.query_params.getlist('drilldown')
        if ddlist:
            for ddstring in ddlist:
                drilldown += ddstring.split('|')

        split = self.get_cell(request, cube, argname='split')
        result = browser.aggregate(
            cell,
            aggregates=aggregates,
            drilldown=drilldown,
            split=split,
            page=request.page,
            page_size=request.page_size,
            order=request.order
        )

        return Response(result.to_dict())


class CubeCell(CubesView):

    def get(self, request, cube_name):
        cube = self.get_cube(request, cube_name)
        browser = self.get_browser(cube)
        self.assert_enabled_action(request, browser, 'cell')

        cell = self.get_cell(request, cube, restrict=True)
        details = browser.cell_details(cell)

        if not cell:
            cell = Cell(cube)

        cell_dict = cell.to_dict()
        for cut, detail in zip(cell_dict["cuts"], details):
            cut["details"] = detail

        return Response(cell_dict)


class CubeReport(CubesView):

    def make_report(self, request, cube_name):
        cube = self.get_cube(request, cube_name)
        browser = self.get_browser(cube)
        self.assert_enabled_action(request, browser, 'report')

        report_request = request.DATA
        try:
            queries = report_request["queries"]
        except KeyError:
            message = "Report request does not contain 'queries' key"
            logging.error(message)
            raise ParseError(detail=message)

        cell = self.get_cell(request, cube, restrict=True)
        cell_cuts = report_request.get("cell")

        if cell_cuts:
            # Override URL cut with the one in report
            cuts = [cut_from_dict(cut) for cut in cell_cuts]
            cell = Cell(cube, cuts)
            logging.info(
                "Using cell from report specification (URL parameters are ignored)"
            )

            if CubesView.workspace.authorizer:
                cell = CubesView.workspace.authorizer.restricted_cell(
                    request.user, cube=cube, cell=cell
                )
        else:
            if not cell:
                cell = Cell(cube)
            else:
                cell = cell

        report = browser.report(cell, queries)
        return Response(report)

    def get(self, request, cube_name):
        return self.make_report(request, cube_name)

    def post(self, request, cube_name):
        return self.make_report(request, cube_name)


class CubeFacts(CubesView):

    def get(self, request, cube_name):
        cube = self.get_cube(request, cube_name)
        browser = self.get_browser(cube)
        self.assert_enabled_action(request, browser, 'facts')

        # Construct the field list
        fields_str = request.query_params.get('fields')
        if fields_str:
            attributes = cube.get_attributes(fields_str.split(','))
        else:
            attributes = cube.all_attributes

        # TODO
        fields = [attr.ref for attr in attributes]
        print('fields:', fields)
        fields = [] #'webshop_sales.id']
        cell = self.get_cell(request, cube, restrict=True)

        # Get the result
        facts = browser.facts(
            cell,
            fields=fields,
            page=request.page,
            page_size=request.page_size,
            order=request.order
        )

        return Response(facts)


class CubeFact(CubesView):

    def get(self, request, cube_name, fact_id):
        cube = self.get_cube(request, cube_name)
        browser = self.get_browser(cube)
        self.assert_enabled_action(request, browser, 'fact')
        fact = browser.fact(fact_id)
        return Response(fact)


class CubeMembers(CubesView):

    def get(self, request, cube_name, dimension_name):
        cube = self.get_cube(request, cube_name)
        browser = self.get_browser(cube)
        self.assert_enabled_action(request, browser, 'members')

        try:
            dimension = cube.dimension(dimension_name)
        except KeyError:
            message = "Dimension '%s' was not found" % dimension_name
            logging.error(message)
            raise ParseError(detail=message)

        hier_name = request.query_params.get('hierarchy')
        hierarchy = dimension.hierarchy(hier_name)

        depth = request.query_params.get('depth', None)
        level = request.query_params.get('level', None)

        if depth and level:
            message = "Both depth and level provided, use only one (preferably level)"
            logging.error(message)
            raise ParseError(detail=message)
        elif depth:
            try:
                depth = int(depth)
            except ValueError:
                message = "depth should be an integer"
                logging.error(message)
                raise ParseError(detail=message)
        elif level:
            depth = hierarchy.level_index(level) + 1
        else:
            depth = len(hierarchy)

        cell = self.get_cell(request, cube, restrict=True)
        values = browser.members(
            cell,
            dimension,
            depth=depth,
            hierarchy=hierarchy,
            page=request.page,
            page_size=request.page_size
        )

        result = {
            "dimension": dimension.name,
            "hierarchy": hierarchy.name,
            "depth": len(hierarchy) if depth is None else depth,
            "data": values
        }

        return Response(result)
