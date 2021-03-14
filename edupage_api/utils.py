import gzip, base64


class GradeUtil:
    def __init__(self, grade_data):
        self.data = grade_data

    def id_to_teacher(self, teacher_id):
        if teacher_id == None:
            return None

        teachers = self.data.get("ucitelia")

        # this dict contains data about the
        # date when this teacher was employed
        # or when will he/she retire / is planned quit this job
        # (datefrom, dateto)
        teacher = teachers.get(teacher_id)

        teacher_name = teacher.get("firstname") + " " + teacher.get("lastname")

        return teacher_name


class IdUtil:
    def __init__(self, data):
        self.data = data
        self.dbi = data.get("dbi")

    def id_to_class(self, c_id):
        if c_id == None:
            return None

        return self.dbi.get("classes").get(c_id).get("name")

    def id_to_teacher(self, t_id):
        if t_id == None:
            return None

        teacher_data = self.dbi.get("teachers").get(t_id)
        teacher_full_name = teacher_data.get(
            "firstname") + " " + teacher_data.get("lastname")
        return teacher_full_name

    def id_to_classroom(self, c_id):
        if c_id == None:
            return None

        return self.dbi.get("classrooms").get(c_id).get("short")

    def id_to_subject(self, s_id):
        if s_id == None:
            return s_id
        return self.dbi.get("subjects").get(s_id).get("short")


class RequestUtil:
    # Almost all of Edupage's API calls go through an 'encryption'
    # They are compressed and encoded with a weird for-loop.

    # This is their original code:
    """
	var encoder = new TextEncoder()
	var gz = new Zlib.RawDeflate(encoder.encode(cs));
	var compressed = gz.compress();
	var cs1 = '';

	for (var i=0;i<compressed.length;i += 10000) {
		cs1 += String.fromCharCode.apply(null, compressed.subarray(i, i+10000));
	}
	cs0 = 'dz:'+btoa(cs1); 

	"""
    @staticmethod
    def encrypt_request_data(data):
        compressed = gzip.compress(data.encode('utf-8'))

        output = RequestUtil.from_char_code(*list(compressed))
        return base64.b64encode(output.encode()).decode()

    @staticmethod
    def from_char_code(*args):
        return ''.join(map(chr, args))
