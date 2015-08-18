from fap_back import *

inited = False

class DecodeError(Exception): pass
class NMEAError(DecodeError): pass
class GPRMCError(NMEAError): pass
class GPRMCFieldNumberError(GPRMCError): pass
class ChecksumError(NMEAError): pass

import operator
def checksum(sentence):
	nmeadata,cksum = sentence.split('*', 1)
	calc_cksum = reduce(operator.xor, (ord(s) for s in nmeadata), 0)
	res = hex(calc_cksum)[2:]
	return cksum == res, cksum, res.upper()

def prep_GPRMC(packet):
	"""Libfap GPRMC is overly strict, this passes exceptions as warnings, but still attempts packet parsing for GPRMC. """
	error = None
	if r':$GPRMC' in packet:
		l,r = packet.split(':$', 1)
		r = r.replace(',,', ', ,').replace(',,', ', ,')
		r_chunks = r.split(',')
		original_ck = checksum(r)
		if not original_ck[0]:
			error = ChecksumError('The checksum was %s; it should be %s. ' % original_ck[1:])
		if r_chunks[2].upper() == 'V':
			r_chunks[2] = 'A'
		try:
			r_chunks[12] = r_chunks[12][:-2] + checksum(','.join(r_chunks))[2]
		except:
			error = GPRMCError('Invaild GPRMC string')
		packet = l + ':$' + ','.join(r_chunks)
	return packet, error


def ErrorWithPtr(e):
	err_type = DecodeError
	if e is None:
		o = ''
	else:
		o = sa_decode_error(e)
		if o == 'Invalid checksum in NMEA sentence':
			err_type = ChecksumError
		if o == 'Less than ten fields in GPRMC sentence':
			err_type = GPRMCFieldError
	return err_type(o)
	
what_to_keep = {
	'altitude': double_p_value,
	'latitude': double_p_value,
	'longitude': double_p_value,
	'src_callsign': None,
	'dst_callsign': None,
	'body': None,
	'header': None,
	'type': None,
	'path': None,
	'path_len': None,
}
class Packet(object):
	def __init__(self,packet, raise_errors = True):
		init()
		self.error = None
		fp = None
		self.should_release = False
		if isinstance(packet, fap_packet_t):
			fp = packet
		if isinstance(packet, str):
			self.should_release = True
			packet, err = prep_GPRMC(packet)
			if err:
				self.error = err
			#print packet
			fp = fap_parseaprs(packet, len(packet), 0)
				
		if fp.error_code is not None:
			self.error = ErrorWithPtr(fp.error_code)
		
		for name, func  in what_to_keep.items():
			val = getattr(fp, name)
			if val is not None and func is not None:
				val = func(val)
			setattr(self, name, val)
		
		if raise_errors and self.error:
			self.error.packet = self
			raise(self.error)
		
		fap_free(fp)
		


			
def init():
	global inited
	if not inited:
		fap_init()
		inited = True

def cleanup():
	global inited
	if inited:
		fap_cleanup()
		inited = False

if __name__ == "__main__":	
	init()
	p = Packet(r'KF7DEI-3>APT312,WIDE2-2:/132932h4012.17N/11019.28WO075/016/A=023420')
	print p.src_callsign
	print p.latitude,p.longitude
	#p = Packet("TEST1>WIDE2-2:/PKWDPOS,142901,A,4011.4851,N,11023.1464,W,0.28,28,100812,1774.3*25")
	cleanup()