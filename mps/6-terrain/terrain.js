const ILLINI_ORANGE = [1, 0.373, 0.02]
const DIFFUSE_TONE = [1, .7, .3]
const SOURCE_TONE = [.9, 1, 1]
const IDENTITY_MATRIX_4 = new Float32Array([1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1])
/**
 * Given the source code of a vertex and fragment shader, compiles them,
 * and returns the linked program.
 */
function compileShader(vs_source, fs_source) {
  const vs = gl.createShader(gl.VERTEX_SHADER)
  gl.shaderSource(vs, vs_source)
  gl.compileShader(vs)
  if (!gl.getShaderParameter(vs, gl.COMPILE_STATUS)) {
    console.error(gl.getShaderInfoLog(vs))
    throw Error("Vertex shader compilation failed")
  }

  const fs = gl.createShader(gl.FRAGMENT_SHADER)
  gl.shaderSource(fs, fs_source)
  gl.compileShader(fs)
  if (!gl.getShaderParameter(fs, gl.COMPILE_STATUS)) {
    console.error(gl.getShaderInfoLog(fs))
    throw Error("Fragment shader compilation failed")
  }

  const program = gl.createProgram()
  gl.attachShader(program, vs)
  gl.attachShader(program, fs)
  gl.linkProgram(program)
  if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
    console.error(gl.getProgramInfoLog(program))
    throw Error("Linking failed")
  }

  // loop through all uniforms in the shader source code
  // get their locations and store them in the GLSL program object for later use
  const uniforms = {}
  for (let i = 0; i < gl.getProgramParameter(program, gl.ACTIVE_UNIFORMS); i += 1) {
    let info = gl.getActiveUniform(program, i)
    uniforms[info.name] = gl.getUniformLocation(program, info.name)
  }
  program.uniforms = uniforms

  return program
}


/**
 * Creates a Vertex Array Object and puts into it all of the data in the given
 * JSON structure, which should have the following form:
 * 
 * ````
 * {"triangles": a list of of indices of vertices
 * ,"attributes":
 *  [ a list of 1-, 2-, 3-, or 4-vectors, one per vertex to go in location 0
 *  , a list of 1-, 2-, 3-, or 4-vectors, one per vertex to go in location 1
 *  , ...
 *  ]
 * }
 * ````
 * 
 * @returns an object with four keys:
 *  - mode = the 1st argument for gl.drawElements
 *  - count = the 2nd argument for gl.drawElements
 *  - type = the 3rd argument for gl.drawElements
 *  - vao = the vertex array object for use with gl.bindVertexArray
 */
function setupGeomery(geom) {
  var triangleArray = gl.createVertexArray()
  gl.bindVertexArray(triangleArray)

  for (let i = 0; i < geom.attributes.length; i += 1) {
    let data = geom.attributes[i]
    supplyDataBuffer(data, i)
  }

  var indices = new Uint16Array(geom.triangles.flat())
  var indexBuffer = gl.createBuffer()
  gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, indexBuffer)
  gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, indices, gl.STATIC_DRAW)

  return {
    mode: gl.TRIANGLES,
    count: indices.length,
    type: gl.UNSIGNED_SHORT,
    vao: triangleArray
  }
}

/**
 * Sends per-vertex data to the GPU and connects it to a VS input
 * 
 * @param data    a 2D array of per-vertex data (e.g. [[x,y,z,w],[x,y,z,w],...])
 * @param loc     the layout location of the vertex shader's `in` attribute
 * @param mode    (optional) gl.STATIC_DRAW, gl.DYNAMIC_DRAW, etc
 * 
 * @returns the ID of the buffer in GPU memory; useful for changing data later
 */
function supplyDataBuffer(data, loc, mode) {
  if (mode === undefined) mode = gl.STATIC_DRAW

  const buf = gl.createBuffer()
  gl.bindBuffer(gl.ARRAY_BUFFER, buf)
  const f32 = new Float32Array(data.flat())
  gl.bufferData(gl.ARRAY_BUFFER, f32, mode)

  gl.vertexAttribPointer(loc, data[0].length, gl.FLOAT, false, 0, 0)
  gl.enableVertexAttribArray(loc)

  return buf;
}

/** Draw one frame */
function draw(seconds) {

  // gl.clearColor(...[1,1,1,1]) // f(...[1,2,3]) means f(1,2,3)
  gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT)
  gl.useProgram(program)

  gl.bindVertexArray(geom.vao)

  let VIEW_CONSTANT = .5
  let goodView = mul([3, 1, 1.5], VIEW_CONSTANT)

  let v = m4view(goodView, [0, 0, 0], [0, 0, 1])
  let rotatingV = m4mul(v, m4rotZ(seconds))

  let ld = normalize([0, 0, 1])
  let h = normalize(add(ld, rotatingV))

  gl.uniform3fv(program.uniforms.lightdir, ld)
  gl.uniform3fv(program.uniforms.lightcolor, [1, 1, 1])
  gl.uniform3fv(program.uniforms.halfway, h)

  gl.uniformMatrix4fv(program.uniforms.m, false, IDENTITY_MATRIX_4)
  gl.uniformMatrix4fv(program.uniforms.v, false, rotatingV)
  gl.uniformMatrix4fv(program.uniforms.p, false, p)

  gl.drawElements(geom.mode, geom.count, geom.type, 0)
}



/** Compute any time-varying or animated aspects of the scene */
function tick(milliseconds) {
  let seconds = milliseconds / 1000;

  draw(seconds)
  requestAnimationFrame(tick)
}

// Generates a list of n random 3D-plane surface normals
function nRandomNormals(n) {
  normals = []
  for (let i = 0; i < n; i += 1) {
    theta = Math.random() * Math.PI * 2;
    normals.push([Math.cos(theta), Math.sin(theta), 0])
  }
  return normals
}

// Generates a list of n random floating xy-points within a boundary
function nRandomPoints(n, xmin = -1, ymin = -1, xmax = 1, ymax = 1) {
  points = []
  for (let i = 0; i < n; i += 1) {
    x = Math.random() * (xmax - xmin) + xmin;
    y = Math.random() * (ymax - ymin) + ymin;
    points.push([x, y, 0])
  }
  return points
}

// Returns a boolean depending on which side of a fault line
// a point lays. 
// true -> Should be raised
function pointShouldBeRaised(x, y, n, p) {
  b = [x, y, 0]
  return dot(sub(b, p), n) >= 0 ? true : false
}

// Returns a procedurally generated grid mesh of gridsize x gridsize points
// This grid will represent a terrain that has `n` faultlines applied to it to modify
// its 'bumpyness'
//
//  "example_grid_strucutre": {
//   "triangles": [],
//   "attributes": [[], [], []]  // position, color, surface normals
// }
function generateGridMesh(gridsize, nFaults) {
  const LOW_X = -1;
  const LOW_Y = -1;
  const HIGH_X = 1;
  const HIGH_Y = 1;
  const MAX_HEIGHT = 1;

  g = {
    "triangles": [],
    "attributes": [[], [], []]  // position, color, surface normals
  }

  if (gridsize < 2 || gridsize > 255) {
    return g;
  }

  const stepSize = 2.0 / (gridsize - 1);

  let minHeight = 0;
  let maxHeight = 0;

  let planes = nRandomNormals(nFaults);
  let points = nRandomPoints(nFaults);

  let positions = [];
  // Generate vertices and colors
  for (let i = 0; i < gridsize; i++) {
    for (let j = 0; j < gridsize; j++) {
      const x = LOW_X + (i * stepSize);
      const y = LOW_Y + (j * stepSize);

      // Apply Faults
      let z = 0;
      for (let k = 0; k < nFaults; k += 1) {
        z += pointShouldBeRaised(x, y, planes[k], points[k]) ? 1 : -1;
      }
      maxHeight = Math.max(maxHeight, z);
      minHeight = Math.min(minHeight, z);
      positions.push([x, y, z]);
      g.attributes[1].push(ILLINI_ORANGE);
    }
  }

  if (minHeight != maxHeight) {
    // Normalize heigts
    positions = positions.map(p => {
      const normHeight = MAX_HEIGHT * (p[2] - (1 / 2) * (maxHeight + minHeight)) / (maxHeight - minHeight);
      return [p[0], p[1], normHeight];
    });
  }

  g.attributes[0] = positions

  // Generate normals
  let normals = [];
  for (let j = 0; j < gridsize; j++) {
    for (let i = 0; i < gridsize; i++) {
      const idx = j * gridsize + i;

      // Get vertices with edge tolerance
      const n = j > 0 ? positions[(j - 1) * gridsize + i] : positions[idx];
      const s = j < gridsize - 1 ? positions[(j + 1) * gridsize + i] : positions[idx];
      const w = i > 0 ? positions[j * gridsize + (i - 1)] : positions[idx];
      const e = i < gridsize - 1 ? positions[j * gridsize + (i + 1)] : positions[idx];

      // Compute normal using cross product of grid vectors
      let normal = normalize(cross(sub(n, s), sub(w, e)))
      // Check if any component is NaN and replace with zero vector if so
      if (isNaN(normal[0]) || isNaN(normal[1]) || isNaN(normal[2])) {
        normal = [0, 0, 0];
      }
      normals.push(normal);
    }
  }

  g.attributes[2] = normals




  // Generate triangles
  for (let j = 0; j < gridsize - 1; j += 1) {
    for (let i = 0; i < gridsize - 1; i += 1) {
      const baseVertex = j * gridsize + i;
      g.triangles.push(
        baseVertex, baseVertex + 1, baseVertex + gridsize,
        baseVertex + 1, baseVertex + gridsize + 1, baseVertex + gridsize
      );
    }
  }
  console.log("wanted verticies:", gridsize * gridsize)
  console.log("number of vertecies", g.attributes[0].length)
  console.log("number of triangles", g.triangles.length / 3)
  console.log("wanted triangles:", (gridsize - 1) ** 2 * 2)

  return g;
}

/** Resizes the canvas to completely fill the screen */
function fillScreen() {
  let canvas = document.querySelector('canvas')
  document.body.style.margin = '0'
  canvas.style.width = '100vw'
  canvas.style.height = '100vh'
  canvas.width = canvas.clientWidth
  canvas.height = canvas.clientHeight
  canvas.style.width = ''
  canvas.style.height = ''
  if (window.gl) {
    gl.viewport(0, 0, canvas.width, canvas.height)
    // TO DO: compute projection matrix based on the width/height aspect ratio
    window.p = m4perspNegZ(0.1, 25, 1.5, canvas.width, canvas.height)
  }
}

/** Compile, link, set up tetraetry */
window.addEventListener('load', async (event) => {
  window.gl = document.querySelector('canvas').getContext('webgl2')
  let vs = await fetch('vertex.glsl').then(res => res.text())
  let fs = await fetch('fragment.glsl').then(res => res.text())
  let isFirstCall = true

  document.querySelector('#submit').addEventListener('click', event => {

    const gridsize = Number(document.querySelector('#gridsize').value) || 2
    const faults = Number(document.querySelector('#faults').value) || 0
    grid = generateGridMesh(gridsize, faults)

    window.geom = setupGeomery(grid)
    console.log("got here")
    console.log(grid)

    window.geom = setupGeomery(grid)
    fillScreen()
    window.addEventListener('resize', fillScreen)
    if (isFirstCall) {
      requestAnimationFrame(tick)
      isFirstCall = false
    } // asks browser to call tick before first frame
  })

  window.program = compileShader(vs, fs)

  gl.enable(gl.DEPTH_TEST)
  gl.enable(gl.BLEND)
  gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA)


})



