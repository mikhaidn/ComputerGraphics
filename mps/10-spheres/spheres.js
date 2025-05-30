const IDENTITY_MATRIX_4 = new Float32Array([1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1])
const BOX_MAG = 2
const BOX_LOW = -BOX_MAG / 2
const BOX_HIGH = BOX_MAG / 2
const BOX_WIDTH = BOX_HIGH - BOX_LOW
const SPAWN_RANGE = BOX_WIDTH - .4
const HALF_SPAWN_RANGE = SPAWN_RANGE / 2
const RADIUS = .15

let tic = 0
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


function applyBoxBounds(x, l, h, d) {

  if (x <= l) {
    return l + d / 2
  }
  if (x >= h) {
    return h - d / 2
  }
  return x

}

function performDynamics(spheres, seconds) {

  spheres.map(sphere => {
    sphere.position = add(sphere.position, mul(sphere.velocity, seconds))
    sphere.velocity = add(sphere.velocity, mul(sphere.accelaration, seconds))
  })

  return spheres
}

function detectCollisions(spheres) {
  const len = spheres.length

  for (let i = 0; i < len; i++) {
    detectAndHandleCollisionWithWall(spheres[i])

  }
  for (let i = 0; i < len; i++) {
    for (let j = i + 1; j < len; j++) {

      detectandHandleCollisionWithSphere(spheres[i], spheres[j], .9);

    }
  }
  return spheres
}

function detectAndHandleCollisionWithWall(sphere, elasticity = 0.9) {
  for (let dim = 0; dim < 3; dim++) {
    // Check lower bound
    if (sphere.position[dim] - RADIUS <= BOX_LOW) {
      // Reverse velocity + dampen
      sphere.velocity[dim] *= -elasticity
      sphere.position[dim] = BOX_LOW + RADIUS
    }

    // Check upper bound
    else if (sphere.position[dim] + RADIUS >= BOX_HIGH) {
      // Reverse velocity + dampen
      sphere.velocity[dim] *= -elasticity

      sphere.position[dim] = BOX_HIGH - RADIUS
    }
  }
  return
}

function detectandHandleCollisionWithSphere(sphere1, sphere2, elasticity = 0.9) {
  const distance = mag(sub(sphere1.position, sphere2.position));

  const minDistance = RADIUS * 2;


  // If distance is less than diameter, spheres are colliding
  if (distance > minDistance) {
    return
  }

  const collision_normal = normalize(sub(sphere2.position, sphere1.position));

  // Calculate speed in collision direction for each sphere
  const s1 = dot(sphere1.velocity, collision_normal);
  const s2 = dot(sphere2.velocity, collision_normal);

  // Calculate net collision speed
  const s = s1 - s2;

  // Only resolve if objects are moving toward each other
  if (s < 0) return;

  // Calculate mass weights - at the moment, should always be 1/2 
  const w1 = sphere1.mass / (sphere1.mass + sphere2.mass);
  const w2 = sphere2.mass / (sphere1.mass + sphere2.mass);

  // Calculate impulse with elasticity factor
  const impulse1 = -w1 * (1 + elasticity) * s;
  const impulse2 = w2 * (1 + elasticity) * s;

  // Apply impulses in collision direction
  sphere1.velocity = add(
    sphere1.velocity,
    mul(collision_normal, impulse1)
  );

  sphere2.velocity = add(
    sphere2.velocity,
    mul(collision_normal, impulse2)
  );


  // Update positions as well to avoid clumping
  const overlap = minDistance - distance;

  sphere1.position = sub(
    sphere1.position,
    mul(collision_normal, overlap / 2)
  );

  sphere2.position = add(
    sphere2.position,
    mul(collision_normal, overlap / 2)
  );
}


/** Draw one frame */
function draw(seconds) {
  // gl.clearColor(...[1,1,1,1]) // f(...[1,2,3]) means f(1,2,3)
  toc = tic
  tic = seconds
  dt = tic - toc

  gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT)
  gl.useProgram(program)

  gl.bindVertexArray(geom.vao)

  let VIEW_CONSTANT = 1
  let goodView = mul([3, 1, 1.5], VIEW_CONSTANT)

  let camera = m4view(goodView, [0, 0, 0], [0, 0, 1])

  let ld = normalize([0, 1, 1])
  let h = normalize(add(ld, camera))

  gl.uniformMatrix4fv(program.uniforms.v, false, camera)
  gl.uniform3fv(program.uniforms.lightdir, ld)
  gl.uniform3fv(program.uniforms.halfway, h)

  let spheresToRender = window.spheres
  spheresToRender = detectCollisions(spheresToRender)
  spheresToRender = performDynamics(spheresToRender, dt)

  spheresToRender.forEach(sphere => {
    /**
     * 
     * 
     * Example Sphere{
     *   "color": randomNArray(3),
     *   "mass": Number(1),
     *   "position": randomNArray(3),
     *   "velocity": [0, 0, 0],
     *   "accelaration": [0, 0, -gravity]
     * }
     */

    let sphereModel = m4mul(m4trans(...sphere.position), m4scale(RADIUS, RADIUS, RADIUS))

    gl.uniform3fv(program.uniforms.ballcolor, sphere.color)
    gl.uniformMatrix4fv(program.uniforms.m, false, sphereModel)
    gl.uniformMatrix4fv(program.uniforms.p, false, p)

    gl.drawElements(geom.mode, geom.count, geom.type, 0)
  });
}



const RESET_TIME = 15
let counter = 0
/** Compute any time-varying or animated aspects of the scene */
function tick(milliseconds) {
  let seconds = milliseconds / 1000.0;
  let resetSeconds = milliseconds / 1000.0 - counter * RESET_TIME;

  if (resetSeconds > RESET_TIME) {
    window.spheres = generateSpheres(window.nspheres, window.gravity)
    counter += 1
  }
  draw(seconds)
  requestAnimationFrame(tick)
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

// Computes normals and adds as an attribute to the geometry
// from the lighting examples/lectures 
function addNormals(geom) {
  let ni = geom.attributes.length
  geom.attributes.push([])
  for (let i = 0; i < geom.attributes[0].length; i += 1) {
    geom.attributes[ni].push([0, 0, 0])
  }
  for (let i = 0; i < geom.triangles.length; i += 1) {
    let p0 = geom.attributes[0][geom.triangles[i][0]]
    let p1 = geom.attributes[0][geom.triangles[i][1]]
    let p2 = geom.attributes[0][geom.triangles[i][2]]
    let e1 = sub(p1, p0)
    let e2 = sub(p2, p0)
    let n = cross(e1, e2)
    geom.attributes[ni][geom.triangles[i][0]] = add(geom.attributes[ni][geom.triangles[i][0]], n)
    geom.attributes[ni][geom.triangles[i][1]] = add(geom.attributes[ni][geom.triangles[i][1]], n)
    geom.attributes[ni][geom.triangles[i][2]] = add(geom.attributes[ni][geom.triangles[i][2]], n)
  }
  for (let i = 0; i < geom.attributes[0].length; i += 1) {
    geom.attributes[ni][i] = normalize(geom.attributes[ni][i])
  }
}


function randomNArray(n) {
  let arr = []
  for (let i = 0; i < n; i++) {
    arr.push(Math.random())
  }
  return arr
}

function generateSpheres(nSpheres, gravity) {
  let spheres = []

  for (let i = 0; i < nSpheres; i += 1) {
    spheres.push({
      "color": randomNArray(3),
      "mass": Number(1),
      "position": sub(mul(randomNArray(3), SPAWN_RANGE), [HALF_SPAWN_RANGE, HALF_SPAWN_RANGE, HALF_SPAWN_RANGE]),
      "velocity": randomNArray(3),
      "accelaration": [0, 0, -gravity]

    })

  }

  return spheres
}


/** Compile, link, set up grid */
window.addEventListener('load', async (event) => {
  window.gl = document.querySelector('canvas').getContext('webgl2')
  let vs = await fetch('vertex.glsl').then(res => res.text())
  let fs = await fetch('fragment.glsl').then(res => res.text())
  let sphere = await fetch('sphere.json').then(res => res.json())
  addNormals(sphere)

  window.nspheres = 50;
  window.gravity = 2;


  document.querySelector('#submit').addEventListener('click', event => {
    window.nspheres = Number(document.querySelector('#spheres').value) || 2
    window.gravity = Number(document.querySelector('#gravity').value) || 0

    window.spheres = generateSpheres(window.nspheres, window.gravity)
  })

  window.spheres = generateSpheres(window.nspheres, window.gravity)

  window.program = compileShader(vs, fs)

  gl.enable(gl.DEPTH_TEST)


  window.geom = setupGeomery(sphere)
  fillScreen()
  window.addEventListener('resize', fillScreen)

  requestAnimationFrame(tick)
})



