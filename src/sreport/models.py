from mongoengine import DateTimeField, Document, \
  ListField, ReferenceField, StringField, DictField
from django import forms
from mongodbforms import DocumentForm




class SpliceServer(Document):
    uuid = StringField(required=True, unique=True)
    description = StringField() # Example what datacenter is this deployed to, i.e. us-east-1
    hostname = StringField(required=True)
    
    def __unicode__(self):
        return u'%s %s' % (self.description, self.hostname)

class SpliceServerRelationships(Document):
    self = ReferenceField(SpliceServer, required=True)
    parent = ReferenceField(SpliceServer)
    children = ListField(ReferenceField(SpliceServer))


class ConsumerIdentity(Document):
    uuid = StringField(required=True, unique=True)  # matches the identifier from the identity certificate
    products = ListField(StringField())

    def __str__(self):
        return  '%s' % (self.uuid)

class ProductUsage(Document):
    consumer = StringField(required=True)
    splice_server = ReferenceField(SpliceServer, required=True)
    instance_identifier = StringField(required=True) # example: MAC Address
    product_info = ListField(StringField())
    facts = DictField()
    date = DateTimeField(required=True)

    def __str__(self):
        return "Consumer '%s' on Splice Server '%s' from instance '%s' using products '%s' at '%s'" % \
               (self.consumer, self.splice_server, self.instance_identifier, self.product_info, self.date)


class ProductUsageForm(DocumentForm):
    #works
    class Meta:
        document = ProductUsage
        #consumer = document.consumer.choicesI
        fields = ['splice_server', 'consumer']
        #fields = ['consumer', 'splice_server']
    #works
        #consumers = forms.ModelChoiceField(queryset=ConsumerIdentity.objects.all())
        #fields = ['splice_server']
    #uuid = forms.ChoiceField(initial=ConsumerIdentity.objects.all())

    # choices is a list of tuples in the form ("value", "label")
    # We are asking mongo to give us the distinct consumer uuids used by ProductUsage
    consumer_choices = [(rhic_id, rhic_id ) for rhic_id in ProductUsage.objects().distinct("consumer")]
    consumer = forms.ChoiceField(required=True, choices=consumer_choices)
    splice_server_choices = [(server_id, server_id) for server_id in ProductUsage.objects().distinct("splice_server")]
    splice_server = forms.ChoiceField(choices=splice_server_choices)

class ConsumerIdentityForm(DocumentForm):
    class Meta:
        document = ConsumerIdentity
        #fields = ['uuid']




        
        