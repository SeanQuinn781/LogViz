import React, { Component } from 'react';

class App extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      // start on the first log/map
      logNum: 0,
      mapContainer: document.getElementById('root'),
      // tooltip styles
      top: 0,
      left: 0,
      // tooltip data
      visits: 0,
      status: 0,
      ip: 0,
      os: 0,
      request: 0
    };
  }

  componentDidMount() {
    this.setData();
    this.setDimensions();
    this.createGraph();
    this.addEvents();
  }

  setData (currentLogNum) {
    let logNum = currentLogNum ? currentLogNum : this.state.logNum;
    this.worldData = topojson.feature(worldData, worldData.objects.countries)
    // loading initial response that loads data
    // and raster from locations.json into page
    console.log('in setData lognum is', logNum)
    this.raster = LOCATIONS[logNum]["raster"];
    this.rasterInfo = LOCATIONS[logNum]["information"];
    // deriving some constants from the info
    this.dx = this.rasterInfo["dx"]
    this.dy = this.rasterInfo["dy"]
    this.raster = this.raster.map((e, index) => {
      let [xy, visits, status, ip, os, fullLogLine] = e;
      return ([
        [
          // x coordinate - int
          xy[0] + d3.randomUniform(-this.dx, this.dx)() / 2,
          // y coordinate - int
          xy[1] + d3.randomUniform(-this.dy, this.dy)() / 2
        ],
        visits,
        status,
        ip,
        os,
        fullLogLine,
        // use data point's index and IP to set a unique ID
        index + '-ip-' + parseInt(ip)
      ])
    })
    // creating graticules
    this.graticule = d3.geoGraticule()
      .step([10, 10]);
  }

  setDimensions() {
    console.log('setting dimensions')
    // dims for graph
    this.boundingRect = this.state.mapContainer.getBoundingClientRect();
    this.height = this.boundingRect.height;
    this.width = this.boundingRect.width;
    // derived quantities
    this.center = [this.width / 2, this.height / 2]
    this.dim = [this.width, this.height]
  }

  createGraph() {
    console.log('creating graph')
    // defining projection
    this.projection = d3.geoNaturalEarth1().scale(1).rotate(90)
      .fitSize([d3.max(this.dim), d3.min(this.dim)], this.worldData)
    // defining geoPath generator
    this.geoPath = d3.geoPath().projection(this.projection)
    // defining scales, most number of visits of a square
    this.maxVisit = d3.max(this.raster.map((e) => {
      return e[1]
    }))
    this.radiusFromVisits = d3.scalePow()
      .domain([0, this.maxVisit])
      .range([0, 2]).exponent(0.2)
    this.opacityFromVisits = d3.scalePow()
      .domain([0, this.maxVisit])
      .range([0, 1]).exponent(0.2)
    // creating circle path constructor
    this.circle = d3.geoCircle()
      .radius((d) => {
        return this.radiusFromVisits(d[1])
      })
      .center((d) => {
        return d[0]
      })
    // 2. Plot data, rm previous svg
    d3.select("svg#LogViz").remove();
    this.svg = d3.select(this.refs.svgMap)
      .append("svg")
        .attr("height", d3.min(this.dim))
        .attr("width", d3.max(this.dim))
        .attr("class", "svgMap")
    // plot graticules
    this.svg.append("path")
      .attr("class", "graticule")
      .datum(this.graticule)
      .attr("d", this.geoPath)
      .style("fill", "none")
      .style("stroke", "#ccc");
    // plot globe
    this.svg.selectAll(".segment")
      .data(this.worldData.features)
      .enter().append("path")
      .attr("class", "segment")
      .attr("d", this.geoPath)
      .style("stroke-width", "1px")
      .style("opacity", ".6");
    // plot raster data
    this.svg.selectAll("circle")
      .data(this.raster)
      .enter().append("path")
      .attr("class", "marker")
      .attr("d", (d) => {
        return this.geoPath(this.circle(d))
      })
      .attr("class", (d) => {
        // get first digit of status code (simple way to color code requests on frontend)
        return 'request-' + d[2].slice(0, 1)
      })
      .attr("opacity", (d) => {
        return this.opacityFromVisits(d[1])
      })
      .attr("id", (d) => {
        return 'id-' + d[6]
      })
      // Tooltips
      .on("mouseover", (data) => {
        // use jquery to select d3 dom nodes
        const dataPointSelect = d3.select("#" + 'id-' + data[6]),
          dataPoint = dataPointSelect._groups[0],
          offset = parseInt($(dataPoint).offset().top),
          offsetLeft = parseInt($(dataPoint).offset().left);

        // create tooltip, could pass in render
        const [xy, visits, status, ip, os, request] = data;

        this.setState({
          // tooltip styles
          top: offset,
          left: offsetLeft,
          // tooltip data
          visits: visits,
          status: status,
          ip: ip,
          os: os,
          request: request
        })
    });
  }

  MapNavigation = () => {
    return <div id="map-navigation">
      {
        LOGLIST.map((log, index) => {
          return <button
            className="map-nav-btn"
            key={index}
            value={index}
            onClick={this.handleClick}
          >
            {log}
          </button>
        })
      }
    </div>;
  }
  handleClick = (e) => {
    let logNum = e.target.value;
    // now that we have changed log files, build a new map
    this.svg.remove()
    e.currentTarget.className = e.currentTarget.className + " active";
    let logClass = e.currentTarget.className;
    this.setState({
      logNum: logNum
    }, (logNum) => {

      const previousButtons = document.getElementsByClassName('map-nav-btn');
      $(previousButtons).removeClass('active');
      this.setData(logNum)
      this.setDimensions()
      this.createGraph()
    })
  }

  handleResize() {
    // handling resize
    // just redraw the graph with the new dimensions
    this.setDimensions()
    this.svg.remove()
    this.createGraph()
  }

  addEvents() {
    this.handleResize = this.handleResize.bind(this)
    window.addEventListener("resize", _.debounce(this.handleResize, 100))
  }

  handleIpClick (currIp) {
    const { ip } = this.state;
  }

  ToolTip = () => {
    const { visits, status, ip, request, os } = this.state;
    const ipLink = '/map/' + ip;
    return <span
        className="toolTipText"
        style={{
          visibility: visits ? 'visible' : 'hidden'
        }}
      >
        Visits: {visits}{'\n'}
        Status: {status}{'\n'}
        IP:{'\n'}{ip}{'\n'}
        OS:{'\n'}{os}
        <a href={ipLink} className="ufwIpLink" onMouseDown={this.handleIpClick(ip)}> UFW block IP</a>
        <button>
          {request}
        </button>
      </span>
  }

  render() {
    const { top, left } = this.state;
    return (
      <div
        ref="svgMap"
        id="LogViz"
      >
        {this.MapNavigation()}
        <div
          className="tooltip"
          style={{
            top: top,
            left: left
          }}
        >
          {this.ToolTip()}
        </div>
    </div>
    );
  }
}
