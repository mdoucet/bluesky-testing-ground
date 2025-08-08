"""
Triple Axis Instrument Module
"""
from devices import EnergySelectorDevice

class Instrument:
    def __init__(self, monochromator: EnergySelectorDevice, analyzer: EnergySelectorDevice):
        self.monochromator = monochromator
        self.analyzer = analyzer
        self.useUB = 0  # Default to not using UB matrix

    def move_to_scan_point(self, e_init: float, e_final: float, q: list[float]):
        """Returns the devices to move for a given scan point"""
        if not isinstance(q,list) and not len(q)==3:
            raise ValueError("TripleAxisGeo.getDevices: q not a list of length 3")

        if self.useUB==1:
                ei = float(e_init)
                ef = float(e_final)
                h  = float(q[0])
                k  = float(q[1])
                l  = float(q[2])
                (a2,a3,a4,sgl,sgu,a6) = self.ub.calcangles(ei=ei,ef=ef,qh=h,qk=k,ql=l)
                devlist = ["A1","A2","A3","A4","A5","A6","SmplLowerTilt","SmplUpperTilt"]
                vallist = [a2/2.0,a2,a3,a4,a6/2,a6,sgl,sgu]
                return devlist, vallist
      
        # Initial energy
        a1, a2 = self.monochromator.set(e_init)
        # Final energy
        a5, a6 = self.analyzer.set(e_final)

            
        # Q
        qx = float(q[0])
        qy = float(q[1])
        qz = float(q[2])
        if not (qx==0 and qy==0 and qz==0):
            theta4 = self.measGeo.phiAngle(qx,qy,qz,
                                    a1, self.monochromator.d_spacing,
                                    a5, self.analyzer.d_spacing)
            theta3 = self.measGeo.psiAngle(qx,qy,qz,
                                    a1, self.monochromator.d_spacing,
                                    a5, self.analyzer.d_spacing)

            # Move A3 and A4

