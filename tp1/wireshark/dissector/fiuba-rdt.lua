-- create myproto protocol and its fields
local p_fiubardt = Proto ("fiubardt","FIUBA Reliable data transfer")

local Protocol = ProtoField.uint8("fiubardt.Protocol","Protocol",base.DEC)
local Data_size = ProtoField.uint32("fiubardt.DataSize","DataSize",base.DEC)
local Seq_num = ProtoField.uint32("fiubardt.SeqNum","SeqNum",base.DEC)
local Ack_num = ProtoField.uint32("fiubardt.AckNum","AckNum",base.DEC)
local Syn = ProtoField.bool("fiubardt.Syn","Syn")
local Fin = ProtoField.bool("fiubardt.Fin","Fin")
local Checksum = ProtoField.uint8("fiubardt.Checksum","Checksum",base.DEC)

p_fiubardt.fields = { Protocol, Data_size, Seq_num, Ack_num, Syn, Fin, Checksum }

local function heuristic_checker(buffer, pinfo, tree)
  -- guard for length
  local length = buffer:len()
  if length < 7 then return false end

  p_fiubardt.dissector(buffer, pinfo, tree)
  return true
end

-- myproto dissector function
function p_fiubardt.dissector (buf, pkt, root)
  -- validate packet length is adequate, otherwise quit
  if buf:len() == 0 then return end
  pkt.cols.protocol = p_fiubardt.name

  -- create subtree for myproto
  local subtree = root:add(p_fiubardt, buf(0))
  -- add protocol fields to subtree
  -- the protocol field is the first byte and is a uint8 denoting 0 or 1 for stop and wait or selective repeat
  local protocol_int = buf(0,1):uint()
  local protocol_str = "Unknown"
  if protocol_int == 0 then
    protocol_str = "Stop and Wait"
  elseif protocol_int == 1 then
    protocol_str = "Selective Repeat"
  end

  subtree:add(Protocol, buf(0,1)):append_text(" (" .. protocol_str .. ")")
  subtree:add(Data_size, buf(1,4))
  subtree:add(Seq_num, buf(5,4))
  subtree:add(Ack_num, buf(9,4))
  subtree:add(Syn, buf(13,1))
  subtree:add(Fin, buf(14,1))
  subtree:add(Checksum, buf(15,1))
end

-- Initialization routine
function p_fiubardt.init()
end

p_fiubardt:register_heuristic("udp", heuristic_checker)

-- -- register a chained dissector for port 8002
-- local tcp_dissector_table = DissectorTable.get("udp.port")
-- tcp_dissector_table:add(14000, p_fiubardt)
