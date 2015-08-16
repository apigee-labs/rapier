import base_base

class BaseEntity(base_base.BaseBase):
    
    def __init__(self, url, json_representation, etag):
        super(Base_entity, self).__init__(url, json_representation, etag)
        if 'id' in json_representation:
            self.id = json_representation['id']
        else:
            raise Exception(520, 'server did not provide id property')
        self.etag = None
        
    def is_property_name(self):
        return 'id'
        
    def refresh():
        # issue a GET to refresh this object from API
        if not self.p_self_link:
            raise ValueError('self_link not set')
            
    def update():
        # issue a PATCH or PUT to update this object from API
        if not self.p_self_link:
            raise ValueError('self_link not set')
            
    def delete():
        # issue a DELETE to remove this object from API
        if not self.p_self_link:
            raise ValueError('self_link not set')
                    
    def create_jso(self):
        return {
            'type': self.type,
            } if self.type else
            {}