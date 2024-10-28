const IlliniOrange =[1, 0.373, 0.02, 1]

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
  for(let i=0; i<gl.getProgramParameter(program, gl.ACTIVE_UNIFORMS); i+=1) {
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
function setuptetraery(tetra) {
  var triangleArray = gl.createVertexArray()
  gl.bindVertexArray(triangleArray)

  for(let i=0; i<tetra.attributes.length; i+=1) {
      let data = tetra.attributes[i]
      supplyDataBuffer(data, i)
  }

  var indices = new Uint16Array(tetra.triangles.flat())
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

  gl.bindVertexArray(tetra.vao)
  gl.bindVertexArray(octa.vao)

  // Render Sun
  let VIEW_CONSTANT =1.5
  let goodView = [2*VIEW_CONSTANT,3*VIEW_CONSTANT,2*VIEW_CONSTANT]
  let V = m4view(goodView, [0,0,0], [1,0,0])
  
  
  // A large octahedron (the Sun)
  // fixed at the origin
  // spinning a full rotation once every two seconds
  let sunRotationM = m4rotX(seconds*Math.PI)
  gl.uniformMatrix4fv(program.uniforms.m, false, sunRotationM)
  gl.uniformMatrix4fv(program.uniforms.v, false, V)
  gl.uniformMatrix4fv(program.uniforms.p, false, p)
  gl.drawElements(octa.mode, octa.count, octa.type, 0)
  
  // A smaller octahedron (the Earth)
  // orbiting the Sun once every few seconds
  // spinning like a top several times a second
  
  let eRadius = 2.4  // Distance from Sun
  let eOrbitPeriod = 1/4 // ops
  let eSpin = 2 // rps
  let eSize = .5
  let earthMatrix = m4mul(

    //last 
    m4rotX(seconds*eOrbitPeriod * Math.PI),   // orbit
    m4trans(0, 0, eRadius) ,     // move to orbit  
    m4rotX(seconds *eSpin* Math.PI),    //  spin  
    m4scale(eSize,eSize,eSize) // scale
    //first
  ) 
  gl.uniformMatrix4fv(program.uniforms.m, false, earthMatrix)
  gl.drawElements(octa.mode, octa.count, octa.type, 0)

  // An octahedron (Mars) a little smaller than the Earth
  // 1.6 times as far from the Sun as the Earth
  // orbiting the Sun 1.9 times slower than the Earth
  // spinning like a top 2.2 times slower than the Earth
  let mRadius = eRadius*1.6  // Distance from Sun
  let mOrbitPeriod = eOrbitPeriod/1.9
  let mSpin = eSpin/2.2
  let mSize = eSize*.9
  
  let marsMatrix = m4mul(
    //last 
    m4rotX(seconds*mOrbitPeriod * Math.PI),
    m4trans(0, 0, mRadius) ,
    m4rotX(seconds *mSpin* Math.PI) ,
    m4scale(mSize,mSize,mSize)
    //first
  ) 
  gl.uniformMatrix4fv(program.uniforms.m, false, marsMatrix)
  
  gl.drawElements(octa.mode, octa.count, octa.type, 0)

  // A tetrahedron (the Moon) smaller than the Earth
  // smaller than the Earth
  // orbiting the Earth faster than the Earth orbits the Sun but slower than the Earth spins
  // always presenting the same side of itself to the Earth
  let moonRadius = .75  // Distance from Earth
  let moonSpinOrbit = 1
  let moonSize = eSize * .9
  let moonMatrix = m4mul(
    //last 
    m4rotX(seconds*eOrbitPeriod * Math.PI),   // orbit
    m4trans(0, 0, eRadius) ,     // move to Sun orbit  
    m4rotX(seconds *moonSpinOrbit* Math.PI),    //  spin  
    m4trans(0, 0, moonRadius) ,     // move to Earth orbit  
    m4scale(moonSize,moonSize,moonSize), // scale moon
    m4scale(eSize,eSize,eSize) // scale to earth
    //first
  ) 
  gl.uniformMatrix4fv(program.uniforms.m, false, moonMatrix)
  
  gl.drawElements(tetra.mode, tetra.count, tetra.type, 0)


  // A tetrahedron (Phobos) smaller than Mars
  // orbiting Mars several times faster than Mars spins
  // always presenting the same side of itself to Mars
  let phobosRadius = .75  // Distance from Earth
  let phobosSpinOrbit = 5
  let phobosSize = mSize * .5
  let phobosMatrix = m4mul(
    //last 
    m4rotX(seconds*mOrbitPeriod * Math.PI),   // orbit
    m4trans(0, 0, mRadius) ,     // move to Sun orbit  
    m4rotX(seconds *phobosSpinOrbit* Math.PI),    //  spin  
    m4trans(0, 0, phobosRadius) ,     // move to Earth orbit  
    m4scale(phobosSize,phobosSize,phobosSize), // scale moon
    m4scale(eSize,eSize,eSize) // scale to earth
    //first
  ) 
  gl.uniformMatrix4fv(program.uniforms.m, false, phobosMatrix)
  
  gl.drawElements(tetra.mode, tetra.count, tetra.type, 0)

  // A tetrahedron (Deimos) half the size of Phobos
  // twice as far from Mars as Phobos
  // orbiting Mars only a little faster than Mars spins
  // always presenting the same side of itself to Mars
  
  let deimosRadius = phobosRadius *2  // Distance from Earth
  let deimosSpinOrbit = mOrbitPeriod*1.1
  let deimosSize = phobosSize /2
  let deimosMatrix = m4mul(
    //last 
    m4rotX(seconds*mOrbitPeriod * Math.PI),   // orbit
    m4trans(0, 0, mRadius) ,     // move to Sun orbit  
    m4rotX(seconds *deimosSpinOrbit* Math.PI),    //  spin  
    m4trans(0, 0, deimosRadius) ,     // move to Earth orbit  
    m4scale(deimosSize,deimosSize,deimosSize), // scale moon
    m4scale(eSize,eSize,eSize) // scale to earth
    //first
  ) 
  gl.uniformMatrix4fv(program.uniforms.m, false, deimosMatrix)
  
  gl.drawElements(tetra.mode, tetra.count, tetra.type, 0)
}



/** Compute any time-varying or animated aspects of the scene */
function tick(milliseconds) {
  let seconds = milliseconds / 1000;

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
      gl.viewport(0,0, canvas.width, canvas.height)
      window.p = m4perspNegZ(0.1, 25, 1.5, canvas.width, canvas.height)
  }
}

/** Compile, link, set up tetraetry */
window.addEventListener('load', async (event) => {
  window.gl = document.querySelector('canvas').getContext('webgl2')
  let vs = await fetch('vertex.glsl').then(res => res.text())
  let fs = await fetch('fragment.glsl').then(res => res.text())   
  let tetrahedron = await fetch('tetrahedron.json').then(res => res.json())
  let octahedron = await fetch('octahedron.json').then(res => res.json())

  window.program = compileShader(vs,fs)

  gl.enable(gl.DEPTH_TEST)
  fillScreen()
  window.addEventListener('resize', fillScreen)
  window.tetra = setuptetraery(tetrahedron)
  window.octa = setuptetraery(octahedron)
  requestAnimationFrame(tick) // asks browser to call tick before first frame

})
