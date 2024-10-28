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

const IlliniBlue = new Float32Array([0.075, 0.16, 0.292, 1])


function makeIlliniGeom(color,depth) {
  g = {"triangles":
    [0,1,2
    ,0,2,3
    ,0,3,1
    ]
,"attributes":
    [  [[-.5,-.9]
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
    ,   [Ill
        ,[1.0, 1.0, 0.0, 1]
        ,[0.0, 0.4, 1.0, 1]
        ,[1.0, 0.0, 0.0, 1]
        ]
    ]
}
//   g = {"triangles":
//     [0,1,2
//       ,1,2,3
//       ,4,5,6
//       ,5,6,7
//       ,8,9,10
//       ,9,10,11
//     ]
//     ,"attributes":
//     [ // position
//       [[-.5,-.9,depth]
//       ,[.5,-.9,depth]
//       ,[-.5,-.6,depth]
//       ,[.5,-.6,depth]
//       ,[-.2,-.6,depth] // middle
//       ,[.2,-.6,depth]
//       ,[-.2,.6,depth] // middle
//       ,[.2,.6,depth]
//       ,[-.5,.9,depth]
//       ,[.5,.9,depth]
//       ,[-.5,.6,depth]
//       ,[.5,.6,depth]
//     ]
//     , // color
//     [color
//       ,color
//       ,color
//       ,color
//       ,color
//       ,color
//       ,color
//       ,color
//       ,color
//       ,color
//       ,color
//       ,color
//     ]
//   ]
// }
return g
}  

function draw(milliseconds) {
  gl.clear(gl.COLOR_BUFFER_BIT) 
  gl.useProgram(program)
  
  // values that do not vary between vertexes or fragments are called "uniforms"
  gl.uniform1f(program.uniforms.seconds, milliseconds/1000)
  
  gl.bindVertexArray(geom.vao)
  gl.drawElements(geom.mode, geom.count, geom.type, 0)
}

function tick(milliseconds) {
  draw(milliseconds)
  requestAnimationFrame(tick) // asks browser to call tick before next frame
}

window.addEventListener('load', async (event) => {
  window.gl = document.querySelector('canvas').getContext('webgl2')
  let vs = await fetch('ex04-vertex.glsl').then(res => res.text())
  let fs = await fetch('ex04-fragment.glsl').then(res => res.text())
  window.program = compileShader(vs,fs)
  window.geom = setupGeomery(makeIlliniGeom(IlliniBlue,0))
  requestAnimationFrame(tick) // asks browser to call tick before first frame
})
