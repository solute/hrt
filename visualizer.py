# coding: utf-8

import urlparse, os, json
import config

svgpan_js = """
<script type="text/ecmascript"><![CDATA[
""" + open("SVGPan.js", "rb").read() + """
]]></script>
"""

isvg_js = """
<script type="text/ecmascript"><![CDATA[

        var colorized_els = [];
        var colors = ["#100", "#300", "#500", "#700", "#900", "#a00", "#c00", "#f00"];

        function get_g(el) {
            while (el.nodeName != "g") {
                el = el.parentNode;
                if (!el) return null;
            };
            return el;
        };

        function colorize(g, color) {
            for (var gidx = 0; gidx < g.childNodes.length; gidx++) {
                    var cn = g.childNodes[gidx];
                    if (cn.nodeName == "ellipse") {
                            cn.setAttribute("fill", color);
                            colorized_els.push(cn);
                    };
            };
        };

        function decolorize(color) {
            for (var idx = 0; idx < colorized_els.length; idx++) {
                var cn = colorized_els[idx];
                if (cn.nodeName == "ellipse") {
                    cn.setAttribute("fill", "white");
                };
            };
            colorized_els = [];
        };

        function mouse_over_handler(evt) {
            var target = evt.target;
            var g = get_g(target);
            if (!g) return;

            var id = g.getAttribute("id");

            decolorize("black");

            colorize(g, "#f00");

            function colorize_parents(ids, max_iter) {
                if (max_iter == 0) return;
                if (ids) {
                    for (var idx = 0; idx < ids.length; idx++) {
                        colorize(document.getElementById(ids[idx]), colors[max_iter]);
                        colorize_parents(parents[ids[idx]], max_iter - 1);
                    };
                };
            };
            colorize_parents(parents[id], 6);

            function colorize_children(ids, max_iter) {
                if (max_iter == 0) return;
                if (ids) {
                    for (var idx = 0; idx < ids.length; idx++) {
                        colorize(document.getElementById(ids[idx]), colors[max_iter]);
                        colorize_children(children[ids[idx]], max_iter - 1);
                    };
                };
            };
            colorize_children(children[id], 6);
        };

        var all = document.getElementsByTagName("g");
        for (var idx = 0; idx < all.length; idx++) {
                var g = all[idx];
                if (g.getAttribute("class") == "node") {
                    for (var gidx = 0; gidx < g.childNodes.length; gidx++) {
                            var cn = g.childNodes[gidx];
                            if (cn.setAttribute) {
                                    cn.setAttribute("onmouseover", "mouse_over_handler(evt)");
                            };
                    };
                };
        };


]]></script>
"""

class Visualizer(object):

    def __init__(self):
        self.graph = []
        self.colors = {}
        self.ids = {}
        self.next_id = 0
        self.id_graph = []

    def get_id(self, typ, key):
        if (typ, key) in self.ids:
            return self.ids[(typ, key)]
        else:
            self.next_id += 1
            id = typ + str(self.next_id)
            self.ids[(typ, key)] = id
            return id

    def add_relation(self, url, origin_url):
        self.graph.append((url, origin_url))


    def visualize_json(self):

        graph = []
        for entity, origin in self.graph:
            graph.append({"entity": entity, "origin": origin})

        f = open(config.get("out_file"), "wb")
        f.write(json.dumps(graph, indent = 4, separators = (",", ": ")))
        f.close()

    def visualize_gif(self):
        """ Creates a gif """
        self.create_dot()
        os.system(config.get("dot_cmd") + " " + config.get("dot_file") + " -o " + config.get("out_file") + " -Tgif")

    def visualize_isvg(self):
        """ Creates an interactive SVG-File """
        self.create_dot()

        parents = {}
        children = {}

        for id_entity, id_origin, id_edge in self.id_graph:

            if id_entity not in parents:
                parents[id_entity] = []
            parents[id_entity].append(id_origin)

            if id_origin not in children:
                children[id_origin] = []
            children[id_origin].append(id_entity)


        data_js = """
            <script type="text/ecmascript"><![CDATA[

            var children = #CHILDREN#;
            var parents = #PARENTS#;

            ]]></script>
        """.replace("#CHILDREN#", repr(children)).replace("#PARENTS#", repr(parents))

        os.system(config.get("dot_cmd") + " " + config.get("dot_file") + " -o " + config.get("out_file") + " -Tsvg")

        f = open(config.get("out_file"), "rb")
        svg = f.read()
        f.close()

        svg = svg.replace("</svg>", svgpan_js + data_js + isvg_js + "</svg>")

        f = open(config.get("out_file"), "wb")
        f.write(svg)
        f.close()


    def visualize(self):
        if config.get("out_format") == "gif":
            return self.visualize_gif()
        elif config.get("out_format") == "isvg":
            return self.visualize_isvg()
        elif config.get("out_format") == "json":
            return self.visualize_json()


    def create_dot(self):
        """ Creates the dot-file needed to layout the graph """

        out = []
        out.append("digraph \"" + config.get("url") + "\" {\n")
        out.append("graph [ rankdir=\"LR\" ];\n")
        out.append("ordering = out;\n")
        out.append("ratio = auto;\n")

        uniq = set()

        for entity, origin in self.graph:
            p_origin = self.pretty_url(origin)
            p_entity = self.pretty_url(entity)
            ukey = p_origin + " // " + p_entity
            if ukey not in uniq:
                if not self.is_ignore(entity):
                    if origin <> entity:
                        id_origin = self.get_id("node", p_origin)
                        id_entity = self.get_id("node", p_entity)
                        id_edge = self.get_id("edge", ukey)

                        self.id_graph.append((id_entity, id_origin, id_edge))

                        out.append("\"" + p_origin + "\" [id=\"" + id_origin + "\"];\n")
                        out.append("\"" + p_entity + "\" [id=\"" + id_entity + "\"];\n")
                        out.append("\"" + p_origin + "\" -> \"" + p_entity + "\" [id=\"" + id_edge + "\"] ;\n")
                uniq.add(ukey)

        out.append("\n}")

        f = open(config.get("dot_file"), "wb")
        f.write("".join(out))
        f.close()



    def is_ignore(self, url):
        return False

    def pretty_url(self, url):

        def snipper(el):
            if len(el)> 32:
                el = el[:12] + "..." + el[-12:]
            return el

        parsed = urlparse.urlparse(url)

        parsed = [snipper(el) for el in list(parsed)[1:] if el]

        return "\\n".join(parsed)
