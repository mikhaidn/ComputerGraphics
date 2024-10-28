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
function setupGeomery(geom) {
  var triangleArray = gl.createVertexArray()
  gl.bindVertexArray(triangleArray)

  for(let i=0; i<geom.attributes.length; i+=1) {
    let buf = gl.createBuffer()
    gl.bindBuffer(gl.ARRAY_BUFFER, buf)
    let f32 = new Float32Array(geom.attributes[i].flat())
    gl.bufferData(gl.ARRAY_BUFFER, f32, gl.STATIC_DRAW)
    gl.vertexAttribPointer(i, geom.attributes[i][0].length, gl.FLOAT, false, 0, 0)
    gl.enableVertexAttribArray(i)
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
   * 
   * @param {*} color - a 3 x 1 [0..1] float array
   * @returns a JSON object with "triangles" and "attributes" associated with the Illini Logo
   *          to be used as the input for `setupGeometry` 
   */
  function makeIlliniGeom(color) {
    g = {"triangles":
      [0,1,2
        ,1,2,3
        ,4,5,6
        ,5,6,7
        ,8,9,10
        ,9,10,11
      ]
      ,"attributes":
      [ // position
        [[-.5,-.9]
        ,[.5,-.9]
        ,[-.5,-.6]
        ,[.5,-.6]
        ,[-.2,-.6] // middle
        ,[.2,-.6]
        ,[-.2,.6] // middle
        ,[.2,.6]
        ,[-.5,.9]
        ,[.5,.9]
        ,[-.5,.6]
        ,[.5,.6]
      ]
      , // color
      [color
        ,color
        ,color
        ,color
        ,color
        ,color
        ,color
        ,color
        ,color
        ,color
        ,color
        ,color
      ]
    ]
  }
  return g
}  

/** Draw one frame */
function draw(seconds) {
  
  gl.clear(gl.COLOR_BUFFER_BIT) 
  gl.useProgram(program)
  
  // values that do not vary between vertexes or fragments are called "uniforms"
  gl.uniform1f(program.uniforms.seconds, seconds)

  // Trig translation matrix
  let m = m4trans(.2*Math.cos(seconds),.3*Math.sin(seconds),0)
  
  // Rotation matrix
  let mrot = m4rotZ(seconds)

  // Scaling matrix
  let mscale = m4scale(...[.8*Math.cos(seconds)+.2,.8*Math.cos(seconds)+.2,.8*Math.cos(seconds)+.2])
  gl.uniformMatrix4fv(program.uniforms.m, false, m)


  // set matrix transformations to uniform buffer `m` as used in `vertex.glsl`
  gl.uniformMatrix4fv(program.uniforms.m, false, m4mul(mscale,mrot,m))

  gl.bindVertexArray(geom.vao)
  gl.drawElements(geom.mode, geom.count, geom.type, 0)
  
  
}

/** Compute any time-varying or animated aspects of the scene */
function tick(milliseconds) {
  let seconds = milliseconds / 1000;

  draw(seconds)
  requestAnimationFrame(tick)
}


/** Compile, link, set up geometry */
window.addEventListener('load', async (event) => {
  window.gl = document.querySelector('canvas').getContext('webgl2')
  let vs = await fetch('vertex.glsl').then(res => res.text())
  let fs = await fetch('fragment.glsl').then(res => res.text())
  window.program = compileShader(vs,fs)
  window.geom = setupGeomery(makeIlliniGeom(IlliniOrange))
  requestAnimationFrame(tick) // asks browser to call tick before first frame

})
