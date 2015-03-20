import unittest
import enet
import Pack
import time

class ComponentStub:
    def __init__(self):
        self.comp_id = 0
        self.net_id = 1


class TestEnet(unittest.TestCase):
    def test_enet(self):
        print ("Making sure enet imported successfully...")
        self.assertTrue(enet.enet is not None, "enet could not be imported")


class TestPack(unittest.TestCase):
    def test_pack_object(self):
        print ("Packing sample object data...")
        # Create the packer
        p = Pack.Packer(ComponentStub())
        
        # Register data processors
        p.registerRPC('test', None, [Pack.USHORT, Pack.USHORT, Pack.FLOAT, Pack.FLOAT])
        
        # Test consistency between data sent and received
        data = [0, 0, 1.0, 2.0]
        p.pack('test', data)
        
        processor = p.pack_list[p.pack_index['test']]
        bdata = p.queued_data.pop()[3][4:]
        newdata = processor.getData(bdata)
        
        self.assertEqual(data, newdata, "Packed data does not match")
        
    def test_pack_integer(self):
        print ("Packing negative integer...")
        # Create the packer
        p = Pack.Packer(ComponentStub())
        
        # Register data processors
        p.registerRPC('test', None, [Pack.INT])
        
        # Test consistency between data sent and received
        data = [-50]
        p.pack('test', data)
        
        processor = p.pack_list[p.pack_index['test']]
        bdata = p.queued_data.pop()[3][4:]
        newdata = processor.getData(bdata)
        
        self.assertEqual(data, newdata, "Packed data does not match")
        
    def test_pack_string(self):
        print ("Packing string...")
        # Create the packer
        p = Pack.Packer(ComponentStub())
        
        # Register data processors
        p.registerRPC('test', None, [Pack.STRING])
        
        # Test consistency between data sent and received
        data = ["Blah"]
        p.pack('test', data)
        
        processor = p.pack_list[p.pack_index['test']]
        bdata = p.queued_data.pop()[3][4:]
        newdata = processor.getData(bdata)
        
        self.assertEqual(data, newdata, "Packed data does not match")
        
    def test_pack_two_strings(self):
        print ("Packing 2 strings...")
        # Create the packer
        p = Pack.Packer(ComponentStub())
        
        # Register data processors
        p.registerRPC('test', None, [Pack.STRING, Pack.STRING])
        
        # Test consistency between data sent and received
        data = ["First", "And second"]
        p.pack('test', data)
        
        processor = p.pack_list[p.pack_index['test']]
        bdata = p.queued_data.pop()[3][4:]
        newdata = processor.getData(bdata)
        
        self.assertEqual(data, newdata, "Packed data does not match")
        
    def test_pack_string_before(self):
        print ("Packing string before integer...")
        # Create the packer
        p = Pack.Packer(ComponentStub())
        
        # Register data processors
        p.registerRPC('test', None, [Pack.STRING, Pack.INT])
        
        # Test consistency between data sent and received
        data = ["Blah", 9000]
        p.pack('test', data)
        
        processor = p.pack_list[p.pack_index['test']]
        bdata = p.queued_data.pop()[3][4:]
        newdata = processor.getData(bdata)
        
        self.assertEqual(data, newdata, "Packed data does not match")
        
    def test_pack_string_after(self):
        print ("Packing string after integer...")
        # Create the packer
        p = Pack.Packer(ComponentStub())
        
        # Register data processors
        p.registerRPC('test', None, [Pack.INT, Pack.STRING])
        
        # Test consistency between data sent and received
        data = [9000, "Blah"]
        p.pack('test', data)
        
        processor = p.pack_list[p.pack_index['test']]
        bdata = p.queued_data.pop()[3][4:]
        newdata = processor.getData(bdata)
        
        self.assertEqual(data, newdata, "Packed data does not match")
        
    def test_pack_string_truncated(self):
        print ("Packing string that's too long assuming 255 limit (should be truncated)")
        # Create the packer
        p = Pack.Packer(ComponentStub())
        
        # Register data processors
        p.registerRPC('test', None, [Pack.STRING])
        
        # Test consistency between data sent and received
        data = ["21111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111200000"]
        
        expected_data = ["211111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111112"]
        p.pack('test', data)
        
        processor = p.pack_list[p.pack_index['test']]
        bdata = p.queued_data.pop()[3][4:]
        newdata = processor.getData(bdata)
        
        self.assertEqual(expected_data, newdata, "Packed data does not match")
        

class TestInput(unittest.TestCase):
    def test_input_mask_(self):
        None
    
if __name__ == '__main__':
    unittest.main()
